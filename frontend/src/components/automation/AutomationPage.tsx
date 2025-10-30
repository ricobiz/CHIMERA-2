import React, { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import { PlayIcon, PauseIcon, StopIcon, BeakerIcon } from '../Icons';
import { executionAgent } from '../../agent/executionAgent.ts';
const BASE_URL: string = (import.meta as any)?.env?.REACT_APP_BACKEND_URL || '';

type LogEntry = { ts: number; step: number; action: string; status?: 'ok'|'error'|'warning'|'info'; error?: string };

type Observation = {
  screenshot_base64?: string;
  screenshot_id?: string;
  grid?: { rows: number; cols: number };
  vision?: Array<{ cell: string; label: string; type: string; confidence: number; bbox?: {x:number;y:number;w:number;h:number} }>;
  viewport?: { width: number; height: number };
  status?: string;
  url?: string;
};

const parseCell = (cell?: string): { colIdx: number; rowIdx: number } => {
  if (!cell) return { colIdx: 0, rowIdx: 0 };
  const m = cell.match(/^([A-Z]+)([0-9]+)$/i);
  if (!m) return { colIdx: 0, rowIdx: 0 };
  const letters = m[1].toUpperCase();
  let col = 0;
  for (let i = 0; i < letters.length; i++) {
    col = col * 26 + (letters.charCodeAt(i) - 64);
  }
  col -= 1;
  const row = Math.max(0, parseInt(m[2], 10) - 1);
  return { colIdx: col, rowIdx: row };
};

const AutomationPage: React.FC<{ onClose?: () => void; embedded?: boolean }> = ({ onClose, embedded = false }) => {
  // Core state
  const [taskText, setTaskText] = useState<string>('Register a new Gmail and return login/password');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [agentStatus, setAgentStatus] = useState<string>('IDLE');
  const [runMode, setRunMode] = useState<'ACTIVE'|'PAUSED'|'STOP'>('PAUSED');
  const [observation, setObservation] = useState<Observation | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [askUser, setAskUser] = useState<string | null>(null);
  const [profileId, setProfileId] = useState<string | null>(null);
  const [profileClean, setProfileClean] = useState<boolean | null>(null);
  const [profileWarm, setProfileWarm] = useState<boolean>(false);
  const [profileUA, setProfileUA] = useState<string>('');
  const [profileIP, setProfileIP] = useState<string>('');
  const [profileProxy, setProfileProxy] = useState<string>('');

  // UX: avoid jumpy autoscroll while user reads
  const [autoScrollLogs, setAutoScrollLogs] = useState<boolean>(false);
  const [userReadingLogs, setUserReadingLogs] = useState<boolean>(false);

  // Viewer state
  const [showGrid, setShowGrid] = useState<boolean>(true);
  const [gridPreset, setGridPreset] = useState<'8x6'|'12x8'|'16x12'|'24x16'|'32x24'|'48x32'|'64x48'>('64x48');
  const [showFullscreen, setShowFullscreen] = useState<boolean>(false);
  const [displaySrc, setDisplaySrc] = useState<string | null>(null);
  const [pendingSrc, setPendingSrc] = useState<string | null>(null);
  const [showDetections, setShowDetections] = useState<boolean>(true);
  // Quick test controls
  const [quickUrl, setQuickUrl] = useState<string>('https://google.com');
  const [quickSessionId, setQuickSessionId] = useState<string | null>(null);
  const [quickError, setQuickError] = useState<string | null>(null);

  // Overlay model snapshot in ref so React re-renders don't wipe drawing
  const pinMappingRef = useRef<boolean>(false);
  const [pinMapping, setPinMapping] = useState<boolean>(false);
  const lastSnapshotRef = useRef<{ shotId: string | null; vision: any[]; viewport: Observation['viewport'] | null; grid: Observation['grid'] | null } | null>(null);
  const lastDrawnShotIdRef = useRef<string | null>(null);
  // Single source of truth for current vision for lists/UI (not for canvas)
  const [vision, setVision] = useState<any[]>([]);
  const [planner, setPlanner] = useState<{strategy: string|null, steps: any[]}>({ strategy: null, steps: [] });
  const [showPlan, setShowPlan] = useState<boolean>(true);
  const [analysis, setAnalysis] = useState<any>(null);
  const [showWarmBanner, setShowWarmBanner] = useState<boolean>(false);
  const [importModalOpen, setImportModalOpen] = useState<boolean>(false);
  const [adjustMsg, setAdjustMsg] = useState<string>("");
  const [activeTab, setActiveTab] = React.useState<'screen'|'detections'|'logs'|'chat'>('screen');
  const [isPaused, setIsPaused] = React.useState(false);
  const [chatMessages, setChatMessages] = React.useState<Array<{role:string,text:string}>>([]);
  const [chatInput, setChatInput] = React.useState('');
  const [selectedElement, setSelectedElement] = React.useState<any>(null);
  const [isLiveMode, setIsLiveMode] = React.useState(false);
  const [agentLogs, setAgentLogs] = React.useState<string[]>([]);
  const [isFullscreen, setIsFullscreen] = React.useState(false);
  const [isDrawingMode, setIsDrawingMode] = React.useState(false);
  const [drawingPath, setDrawingPath] = React.useState<Array<{x:number,y:number,time:number}>>([]);
  const [isDrawing, setIsDrawing] = React.useState(false);
  const [savedPaths, setSavedPaths] = React.useState<Array<{name:string,path:Array<{x:number,y:number,time:number}>}>>([]);



  const viewerRef = useRef<HTMLDivElement | null>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const overlayRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  // Zoom disabled for stability

  const logsEndRef = useRef<HTMLDivElement | null>(null);
  const pollRef = useRef<any>(null);

  // Tap feedback on grid
  const [tapCell, setTapCell] = useState<{cell: string; left: number; top: number} | null>(null);

  // Overlay rect aligned to image
  const [overlayRect, setOverlayRect] = useState<{left:number;top:number;width:number;height:number} | null>(null);

  const updateOverlayRect = useCallback(() => {
    const viewer = viewerRef.current;
    const img = imageRef.current;
    if (!viewer || !img) return;
    const vRect = viewer.getBoundingClientRect();
    const iRect = img.getBoundingClientRect();
    const rect = { left: iRect.left - vRect.left, top: iRect.top - vRect.top, width: iRect.width, height: iRect.height };
    setOverlayRect(rect);
    // debug
    // console.debug('[overlay] rect', rect);
  }, []);

  useEffect(() => {
    updateOverlayRect();
    const viewer = viewerRef.current;
    if (!viewer) return;

    // Safe ResizeObserver creation without optional chaining after new
    const ResizeObs: any = (window as any).ResizeObserver;
    let ro: any = null;
    if (ResizeObs) {
      ro = new ResizeObs(() => {
        updateOverlayRect();
      });
      try {
        ro.observe(viewer);
      } catch {}
    }

    const onResize = () => updateOverlayRect();
    window.addEventListener('resize', onResize);

    return () => {
      try { window.removeEventListener('resize', onResize); } catch {}
      if (ro && viewer) {
        try { ro.unobserve(viewer); } catch {}
        try { ro.disconnect(); } catch {}
      }
    };
  }, [updateOverlayRect]);

  // Smooth screenshot swapping
  useEffect(() => {
    if (!pendingSrc) return;
    const img = new Image();
    img.onload = () => { setDisplaySrc(pendingSrc); setTimeout(updateOverlayRect, 50); };
    img.src = `data:image/png;base64,${pendingSrc}`;
  }, [pendingSrc, updateOverlayRect]);

  const scrollToBottom = () => {
    if (userReadingLogs) return; // don't jump while user reads
    try { logsEndRef.current?.scrollIntoView({ behavior: 'smooth' }); } catch {}
  };
  useEffect(() => { if (autoScrollLogs && !userReadingLogs) scrollToBottom(); }, [logs, autoScrollLogs, userReadingLogs]);

  // Poll logs from backend hook
  const loadLogs = async () => {
    try {
      const resp = await fetch(`${BASE_URL}/api/hook/log`);
      const data = await resp.json();
      setLogs(data.logs || []);
      setAgentStatus(data.status || 'IDLE');
      setSessionId(data.session_id || null);
      if (data.ask_user) setAskUser(data.ask_user); else setAskUser(null);
      if (data.profile_id) setProfileId(data.profile_id);
      if (!pinMappingRef.current) {
        const obs = (data.observation || null) as Observation | null;
        setObservation(obs);
        if (obs && obs.vision && obs.vision.length > 0) {
          const v = obs.vision as any[];
          lastSnapshotRef.current = { shotId: obs.screenshot_id || null, vision: v, viewport: obs.viewport || null, grid: obs.grid || null };
          if (obs.screenshot_base64) setPendingSrc(obs.screenshot_base64);
          lastDrawnShotIdRef.current = obs.screenshot_id || null;
      try {
        const ana = (data.analysis || data.observation?.analysis || null);
        setAnalysis(ana);
        const warmReady = !!(ana?.analysis?.availability?.profile?.is_warm);
        setShowWarmBanner(!warmReady);
        if (data.session_id) setSessionId(data.session_id);
        
        // Update profile health info
        const profile_data = ana?.analysis?.availability?.profile || {};
        if (profile_data.user_agent) setProfileUA(profile_data.user_agent);
        if (profile_data.ip) setProfileIP(profile_data.ip);
        if (profile_data.proxy) setProfileProxy(JSON.stringify(profile_data.proxy));
      } catch {}

          setVision(v);
        }
      // Capture plan for overlay
      try {
        const plan = (data.plan || data.observation?.plan || data.observation?.analysis?.plan || null);
        setPlanner({ strategy: plan?.strategy || null, steps: Array.isArray(plan?.steps) ? plan.steps : [] });
      } catch {}

      }
    } catch (e) {
      // silent
    }
  };
  // Sync initial grid preset from backend once
  useEffect(() => {
    (async()=>{ try { 
      const r = await fetch(`${BASE_URL}/api/automation/grid`); 
      const js = await r.json(); 
      const v = `${js.cols || 16}x${js.rows || 24}` as any; 
      const allowed = ['8x6','12x8','16x12','24x16','32x24','48x32','64x48'];
      if (allowed.includes(v)) setGridPreset(v);
    } catch {} })();
  }, []);

  useEffect(() => {
    pollRef.current = setInterval(loadLogs, 1500);
    return () => clearInterval(pollRef.current);
  }, []);

  // Keep pin ref in sync
  useEffect(() => { pinMappingRef.current = pinMapping; }, [pinMapping]);

  const startTask = async () => {
    if (!taskText.trim()) return;
    setIsSubmitting(true);
    try {
      const resp = await fetch(`${BASE_URL}/api/hook/exec`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: taskText, timestamp: Date.now(), nocache: true })
      });
      const data = await resp.json();
      if (resp.ok) {
        setJobId(data.job_id);
        setLogs([]);
        
        if (data.status === 'NEEDS_REQUIREMENTS') {
          // Missing requirements - show warmup banner
          setShowWarmBanner(true);
          setAgentStatus('IDLE');
          alert('⚠️ ' + (data.message || 'Missing requirements'));
        } else {
          setAgentStatus('ACTIVE');
        }
      } else {
        alert(data.detail || 'Failed to start');
      }
    } catch (e: any) {
      alert(e.message || 'Failed to start');
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetTask = async () => {
    try {
      // Close current session if exists
      if (sessionId) {
        try {
          await fetch(`${BASE_URL}/api/automation/session/close`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
          });
        } catch {}
      }
      
      // Clear backend state
      try {
        await fetch(`${BASE_URL}/api/hook/control`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mode: 'STOP' })
        });
      } catch {}
      
      // Clear all frontend state
      setTaskText('');
      setLogs([]);
      setJobId(null);
      setSessionId(null);
      setAgentStatus('IDLE');
      setIsSubmitting(false);
      setDisplaySrc(null);
      setPendingSrc(null);
      setShowWarmBanner(false);
      setVision([]);
      setObservation(null);
      setPlanner({ strategy: null, steps: [] });
      
      alert('✅ Всё сброшено! Можете начать новую задачу.');
    } catch (e: any) {
      console.error('Reset error:', e);
      alert('Ошибка сброса, но состояние очищено');
    }
  };

  const control = async (mode: 'ACTIVE'|'PAUSED'|'STOP') => {
    try {
      const resp = await fetch(`${BASE_URL}/api/hook/control`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mode })
      });
      const data = await resp.json();
      setRunMode(data.run_mode);
      setAgentStatus(data.agent_status);
    } catch (e) {
      // ignore
    }
  };

  const recheckProfile = async () => {
    const id = profileId || prompt('Profile ID to re-check');
    if (!id) return;
    try {
      const resp = await fetch(`${BASE_URL}/api/profile/check`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ profile_id: id }) });
      const data = await resp.json();
      setProfileClean(!!data.is_clean);
      alert(`Profile re-check done. Clean=${data.is_clean ? 'true' : 'false'}`);
    } catch (e: any) {
      alert(e.message || 'Re-check failed');
    }
  };

  // Ghost cursor position from last action
  const ghostCell = useMemo(() => {
    const step = [...(logs||[])].reverse().find(l => l?.action?.includes('CLICK_CELL') || l?.action?.includes('TYPE_AT_CELL') || l?.action?.includes('HOLD_DRAG'));
    const match = step?.action?.match(/[A-Z]+[0-9]{1,2}/)?.[0];
    return match || null;
  }, [logs]);

  const cellToPercent = (cell: string | null, grid?: {rows:number; cols:number}) => {
    if (!cell || !grid) return { left: 50, top: 50 };
    const m = cell.match(/^([A-Z]+)([0-9]+)$/);
    if (!m) return { left: 50, top: 50 };
    const { colIdx, rowIdx } = parseCell(cell);
    const left = ((colIdx + 0.5) / (grid.cols || 8)) * 100;
    const top = ((rowIdx + 0.5) / (grid.rows || 12)) * 100;
    return { left, top };
  };

  // Quick test: create session, navigate and screenshot
  const quickNavigate = async () => {
    try {
      setQuickError(null);
      
      // If user provided a session ID manually, connect to it instead of creating new
      if (quickSessionId && quickSessionId.trim()) {
        const sid = quickSessionId.trim();
        const resp = await fetch(`${BASE_URL}/api/automation/screenshot?session_id=${sid}`);
        const js: any = await resp.json();
        if (!resp.ok || !js?.screenshot_base64) throw new Error(js?.detail || 'Failed to connect to session');
        
        setPendingSrc(js.screenshot_base64);
        setObservation(js);
        const v = (js.vision || []) as any[];
        lastSnapshotRef.current = { shotId: js.screenshot_id || null, vision: v, viewport: js.viewport || null, grid: js.grid || null };
        lastDrawnShotIdRef.current = js.screenshot_id || null;
        setVision(v);
        setSessionId(sid);
        return;
      }
      
      // Otherwise: Use smoke-check for atomic navigate+screenshot+vision
      const resp = await fetch(`${BASE_URL}/api/automation/smoke-check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: quickUrl, use_proxy: false })
      });
      const js: any = await resp.json();
      if (!resp.ok || !js?.screenshot_base64) throw new Error(js?.detail || 'smoke-check failed');
      setPendingSrc(js.screenshot_base64);
      setObservation(js);
      const v = (js.vision || []) as any[];
      lastSnapshotRef.current = { shotId: js.screenshot_id || null, vision: v, viewport: js.viewport || null, grid: js.grid || null };
      lastDrawnShotIdRef.current = js.screenshot_id || null;
      setVision(v);
      setQuickSessionId(js.session_id || null);
      setSessionId(js.session_id || null);
    } catch (e: any) {
      alert(e.message || 'Quick navigate failed');
    }
  };

  const ghostPos = useMemo(() => cellToPercent(ghostCell, observation?.grid), [ghostCell, observation?.grid]);

  const statusPill = (status: string) => {
    switch (status) {
      case 'ACTIVE': return 'bg-green-900/40 text-green-300';
      case 'PAUSED': return 'bg-yellow-900/40 text-yellow-300';
      case 'WAITING_USER': return 'bg-blue-900/40 text-blue-300';
      case 'ERROR': return 'bg-red-900/40 text-red-300';
      default: return 'bg-gray-900/40 text-gray-300';
    }
  };

  // Draw detections on canvas (bound to current overlayRect)
  const drawCanvas = useCallback(() => {
    const cvs = canvasRef.current;
    if (!cvs || !overlayRect) return;
    const ctx = cvs.getContext('2d');
    if (!ctx) return;

    // Size canvas to overlayRect (DPR aware)
    const dpr = (window.devicePixelRatio || 1);
    const targetW = Math.max(1, Math.floor(overlayRect.width * dpr));
    const targetH = Math.max(1, Math.floor(overlayRect.height * dpr));
    if (cvs.width !== targetW || cvs.height !== targetH) {
      cvs.width = targetW;
      cvs.height = targetH;
      cvs.style.width = `${overlayRect.width}px`;
      cvs.style.height = `${overlayRect.height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    } else {
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, overlayRect.width, overlayRect.height);
    }

    if (!showDetections) return;

    const snap = lastSnapshotRef.current;
    if (!snap) return;
    const v = snap.vision || [];
    const vw = snap.viewport?.width || 1280;
    const vh = snap.viewport?.height || 800;

    // Thinner detection borders for clarity on mobile/high-DPI
    ctx.lineWidth = 0.75;
    for (let i=0; i<Math.min(v.length, 50); i++) {
      const el = v[i] as any;
      const b = el.bbox || {};
      const x = (b.x || 0) * overlayRect.width / vw;
      const y = (b.y || 0) * overlayRect.height / vh;
      const w = (b.w || 0) * overlayRect.width / vw;
      const h = (b.h || 0) * overlayRect.height / vh;
      // Box
      ctx.strokeStyle = 'rgba(80, 140, 255, 0.95)';
      ctx.shadowColor = 'rgba(80, 140, 255, 0.5)';
      ctx.shadowBlur = 2;
      ctx.strokeRect(x, y, Math.max(1,w), Math.max(1,h));
      // Label
      const label = `${el.label || el.type || ''} · ${el.cell || ''}`.slice(0, 40);
      if (label) {
        ctx.font = '10px ui-monospace, SFMono-Regular, Menlo, monospace';
        const pad = 3;
        const tw = ctx.measureText(label).width + pad*2;
        const th = 14;
        ctx.fillStyle = 'rgba(0,0,0,0.7)';
        ctx.strokeStyle = 'rgba(80, 140, 255, 0.85)';
        ctx.shadowBlur = 0;
        ctx.fillRect(x, Math.max(0,y-th-2), tw, th);
        ctx.fillRect(x, Math.max(0,y-th-2), tw, th);
        ctx.strokeRect(x, Math.max(0,y-th-2), tw, th);
        ctx.fillStyle = 'rgba(200,220,255,0.95)';
        ctx.fillText(label, x+pad, Math.max(10,y-4));
      }
    }
  }, [overlayRect, showDetections]);

  // Redraw when image rect or overlays change
  useEffect(() => { drawCanvas(); }, [drawCanvas]);

  // Click handler on the screenshot to show calculated cell
  const handleImageClick = (e: React.MouseEvent<HTMLImageElement>) => {
    const img = imageRef.current;
    const view = viewerRef.current;
    if (!img || !view || !overlayRect) return;
    const iRect = img.getBoundingClientRect();
    // compute relative to image (letterboxed)
    const x = (e.clientX - iRect.left) / iRect.width;
    const y = (e.clientY - iRect.top) / iRect.height;
    if (x < 0 || x > 1 || y < 0 || y > 1) return;
    const [cols, rows] = (gridPreset || '24x16').split('x').map(n => parseInt(n, 10));
    const colIndex = Math.min(Math.max(Math.floor(x * cols), 0), cols - 1);
    const rowIndex = Math.min(Math.max(Math.floor(y * rows), 0), rows - 1);
    const colLetter = (() => {
      // number to excel letters
      let n = colIndex + 1; let s = '';
      while (n > 0) { const r = (n - 1) % 26; s = String.fromCharCode(65 + r) + s; n = Math.floor((n - 1) / 26); }
      return s;
    })();
    const cell = `${colLetter}${rowIndex + 1}`;
    // Position label inside overlayRect
    const left = overlayRect.left + ((colIndex + 0.5) / cols) * overlayRect.width;
    const top = overlayRect.top + ((rowIndex + 0.5) / rows) * overlayRect.height;
    const ovLeft = ((left - overlayRect.left) / overlayRect.width) * 100;
    const ovTop = ((top - overlayRect.top) / overlayRect.height) * 100;
    setTapCell({ cell, left: ovLeft, top: ovTop });
    setTimeout(() => setTapCell(null), 1200);
  };

  // Helper for listing detections
  const currentDetections = useMemo(() => {
    return vision || [];
  }, [vision]);

  return (
    <div className="flex flex-col bg-[#0f0f10] text-gray-100 h-screen overflow-hidden">
      {/* Compact Header - Fixed */}
      <div className="px-2 md:px-4 py-2 border-b border-gray-800 flex-shrink-0 bg-[#0f0f10]">
        <div className="flex flex-col md:flex-row items-start md:items-center gap-2">
          <div className="flex items-center gap-2 w-full md:w-auto">
            {onClose && (
              <button onClick={onClose} className="px-2 py-1 bg-gray-800 hover:bg-gray-700 text-white rounded text-xs whitespace-nowrap">← Back</button>
            )}
            <div className="text-sm text-gray-300 whitespace-nowrap">Browser Automation</div>
          </div>
          <div className="flex items-center gap-2 flex-1 w-full md:w-auto min-w-0">
            <input value={quickUrl} onChange={(e:any)=>setQuickUrl(e.target.value)} className="flex-1 min-w-0 px-2 py-1.5 text-xs bg-black/40 border border-gray-700 rounded text-gray-200 placeholder-gray-500" placeholder="https://..." />
            <input value={quickSessionId || ''} onChange={(e:any)=>setQuickSessionId(e.target.value)} className="w-28 md:w-40 px-2 py-1.5 text-xs bg-black/40 border border-gray-700 rounded text-gray-200 placeholder-gray-500" placeholder="session-id" />
            <button title="Connect" onClick={quickNavigate} className="p-1.5 rounded bg-blue-800/70 hover:bg-blue-700/70 border border-blue-700 text-blue-200 flex-shrink-0"><PlayIcon className="w-4 h-4"/></button>
          </div>
          {/* Controls */}
          <div className="flex items-center gap-1 md:gap-2 flex-shrink-0">
            <button onClick={()=>setIsLiveMode(!isLiveMode)} className={`px-2 py-1 text-xs rounded whitespace-nowrap ${isLiveMode?'bg-red-600 text-white':'bg-gray-700 text-gray-300'}`} title="Toggle Live Mode">{isLiveMode?'🔴':'⚪'}</button>
            <button onClick={()=>setIsPaused(!isPaused)} className={`px-2 py-1 text-xs rounded whitespace-nowrap ${isPaused?'bg-yellow-600':'bg-gray-700'} text-white`} title="Pause/Resume">{isPaused?'▶️':'⏸️'}</button>
            <span className={`text-xs px-2 py-1 rounded whitespace-nowrap ${statusPill(agentStatus)}`}>{agentStatus}</span>
          </div>
        </div>
      </div>

      {/* Main Layout: 2 columns - Screen (65%) + Plan (35%) */}
      <div className={`flex-1 flex ${isFullscreen?'flex-col':'flex-col lg:flex-row'} overflow-hidden min-h-0 gap-2 p-2`}>
        
        {/* LEFT: Browser Screen */}
        <div className={`${isFullscreen?'w-full h-full':'w-full lg:w-[65%]'} flex flex-col min-h-0`}>
          <div className="flex items-center justify-between mb-2 px-2">
            <div className="text-sm text-gray-400">Browser View</div>
            <div className="flex gap-2">
              <button onClick={()=>setIsDrawingMode(!isDrawingMode)} className={`px-2 py-1 text-xs rounded ${isDrawingMode?'bg-purple-600 text-white':'bg-gray-700 text-gray-300'}`}>
                ✏️ {isDrawingMode?'Drawing':'Draw Path'}
              </button>
              <button onClick={()=>setIsFullscreen(!isFullscreen)} className="px-2 py-1 text-xs rounded bg-gray-700 text-gray-300 hover:bg-gray-600">
                {isFullscreen?'↙️ Exit':'⛶ Fullscreen'}
              </button>
            </div>
          </div>
          
          <div ref={viewerRef} className={`relative w-full ${isFullscreen?'flex-1':'h-80 md:h-96'} border border-gray-800 rounded bg-black overflow-hidden`} 
            style={{ touchAction: 'none' }}
            onMouseDown={(e)=>{
              if (!isDrawingMode) return;
              setIsDrawing(true);
              const rect = viewerRef.current?.getBoundingClientRect();
              if (!rect) return;
              const x = e.clientX - rect.left;
              const y = e.clientY - rect.top;
              setDrawingPath([{x, y, time: Date.now()}]);
            }}
            onMouseMove={(e)=>{
              if (!isDrawing || !isDrawingMode) return;
              const rect = viewerRef.current?.getBoundingClientRect();
              if (!rect) return;
              const x = e.clientX - rect.left;
              const y = e.clientY - rect.top;
              setDrawingPath(prev=>[...prev, {x, y, time: Date.now()}]);
            }}
            onMouseUp={()=>{
              if (isDrawing && drawingPath.length > 1) {
                // Save path
                const pathName = `Path ${savedPaths.length + 1}`;
                setSavedPaths(prev=>[...prev, {name: pathName, path: drawingPath}]);
                setChatMessages(prev=>[...prev, {role:'system',text:`✏️ Saved ${pathName} with ${drawingPath.length} points`}]);
              }
              setIsDrawing(false);
            }}
            onClick={async (e)=>{
              if (isDrawingMode) return; // Skip click in drawing mode
              
              // Click to select element + remote click (no Ctrl needed)
              const rect = viewerRef.current?.getBoundingClientRect();
              if (!rect) return;
              const x = e.clientX - rect.left;
              const y = e.clientY - rect.top;
              
              // Find clicked element
              let clickedIndex = -1;
              const clicked = vision.find((v:any, idx:number)=>{
                const b = v.bbox;
                const hit = x>=b.x && x<=(b.x+b.w) && y>=b.y && y<=(b.y+b.h);
                if (hit) clickedIndex = idx;
                return hit;
              });
              
              if (clicked) {
                setSelectedElement(clicked);
                const elementNum = clickedIndex + 1;
                setChatMessages(prev=>[...prev, {role:'system',text:`✅ Selected Element #${elementNum}: "${clicked.label || clicked.type}"`}]);
                
                // Auto send remote click (no Ctrl needed)
                if (sessionId) {
                  try {
                    const resp = await fetch(`${BASE_URL}/api/automation/remote-click`, {
                      method: 'POST',
                      headers: {'Content-Type':'application/json'},
                      body: JSON.stringify({
                        session_id: sessionId,
                        x: clicked.bbox.x + clicked.bbox.w/2,
                        y: clicked.bbox.y + clicked.bbox.h/2
                      })
                    });
                    const data = await resp.json();
                    if (data.success) {
                      setChatMessages(prev=>[...prev, {role:'assistant',text:`🖱️ Clicked element #${elementNum}`}]);
                    }
                  } catch(err) {
                    console.error('Remote click failed:', err);
                  }
                }
              }
            }}
          >
          {quickError && (
            <div className="absolute top-2 left-2 right-2 text-[11px] text-red-300 bg-red-900/30 border border-red-800 rounded px-2 py-1 z-30">{quickError}</div>
          )}

          {displaySrc ? (
            <img ref={imageRef} onLoad={updateOverlayRect} onClick={handleImageClick} src={`data:image/png;base64,${displaySrc}`} alt="screenshot" className="max-w-full max-h-full object-contain cursor-crosshair select-none" />
          ) : (
            <div className="text-xs text-gray-600 text-center">No screenshot</div>
          )}

          {/* Grid overlay aligned to image rect */}
          {/* Zoom lens disabled */}
          {/* Plan overlay (top-right) */}
          {showPlan && (planner.steps?.length || 0) > 0 && overlayRect && (
            <div className="absolute right-2 top-2 max-w-[46%] bg-black/55 backdrop-blur-sm border border-gray-700 rounded-lg text-gray-200 shadow-lg" style={{pointerEvents:'auto'}}>
              <div className="flex items-center justify-between px-3 py-2 border-b border-gray-700/60">
                <div className="text-[12px] text-gray-300">Plan: <span className="text-blue-300">{planner.strategy || '—'}</span></div>
                <button onClick={()=> setShowPlan(false)} className="text-[11px] text-gray-400 hover:text-gray-200">Hide</button>
              </div>
              <div className="max-h-48 overflow-y-auto p-3 space-y-2">
                {planner.steps.slice(0, 20).map((s:any, idx:number) => (
                  <div key={s.id || idx} className="text-[11px] leading-snug">
                    <span className="text-gray-400">{idx+1}.</span> <span className="text-gray-100">{s.action}</span>
                    {s.field && (<span className="text-gray-400"> • {s.field}</span>)}
                    {s.target && (<span className="text-gray-400"> • {s.target}</span>)}
                    {s.value && typeof s.value === 'string' && s.value !== '[WAITING_USER_INPUT]' && (<span className="text-gray-500"> • {s.value}</span>)}
                  </div>
                ))}
                {planner.steps.length > 20 && (
                  <div className="text-[10px] text-gray-500">…and {planner.steps.length - 20} more</div>
                )}
              </div>
            </div>
          )}
          {showGrid && overlayRect && (
            <div ref={overlayRef} className="absolute pointer-events-none" style={{ left: overlayRect.left, top: overlayRect.top, width: overlayRect.width, height: overlayRect.height }}>
              <div className="w-full h-full" style={{ backgroundImage: `linear-gradient(rgba(200,200,200,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(200,200,200,0.08) 1px, transparent 1px)`, backgroundSize: `${overlayRect.width/parseInt(gridPreset.split('x')[0],10)}px ${overlayRect.height/parseInt(gridPreset.split('x')[1],10)}px` }} />
            </div>
          )}

          {/* Canvas overlay for detections */}
          {overlayRect && (
            <canvas ref={canvasRef} className="absolute pointer-events-none" style={{ left: overlayRect.left, top: overlayRect.top, width: overlayRect.height, height: overlayRect.height }} />
          )}

          {/* Element numbers overlay */}
          {showDetections && overlayRect && vision.map((v:any, idx:number) => {
            const isSelected = selectedElement === v;
            return (
              <div key={idx} 
                className={`absolute pointer-events-none transition-all ${isSelected?'z-50':'z-40'}`}
                style={{ 
                  left: `${overlayRect.left + v.bbox.x}px`, 
                  top: `${overlayRect.top + v.bbox.y}px`,
                  width: `${v.bbox.w}px`,
                  height: `${v.bbox.h}px`
                }}
              >
                {/* Bounding box */}
                <div className={`w-full h-full border-2 rounded ${isSelected?'border-blue-400 bg-blue-400/20':'border-green-400/60 hover:border-green-300'}`} />
                
                {/* Element number badge */}
                <div className={`absolute -top-2 -left-2 px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${isSelected?'bg-blue-500 text-white':'bg-green-500/90 text-white'}`}>
                  #{idx + 1}
                </div>
                
                {/* Label on hover */}
                {v.label && (
                  <div className="absolute bottom-full left-0 mb-1 px-2 py-1 bg-black/80 text-white text-[10px] rounded whitespace-nowrap max-w-xs truncate opacity-0 hover:opacity-100 transition-opacity">
                    {v.label}
                  </div>
                )}
              </div>
            );
          })}

          {tapCell && overlayRect && (
            <div className="absolute" style={{ left: `${overlayRect.left + (tapCell.left/100)*overlayRect.width}px`, top: `${overlayRect.top + (tapCell.top/100)*overlayRect.height}px`, transform: 'translate(-50%, -50%)' }}>
              <div className="px-1.5 py-0.5 text-[10px] rounded bg-black/80 border border-gray-600 text-gray-100">{tapCell.cell}</div>
            </div>
          )}

          {ghostCell && overlayRect && (
            <div className="absolute transition-all duration-300" style={{ left: `${overlayRect.left + (ghostPos.left/100)*overlayRect.width}px`, top: `${overlayRect.top + (ghostPos.top/100)*overlayRect.height}px`, transform: 'translate(-50%, -50%)' }}>
              <div className="w-4 h-4 rounded-full bg-white/90 shadow-[0_0_10px_rgba(255,255,255,0.6)] border border-gray-200" />
            </div>
          )}
          
          {/* Drawing path overlay */}
          {isDrawingMode && drawingPath.length > 0 && (
            <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{zIndex: 100}}>
              <polyline 
                points={drawingPath.map(p=>`${p.x},${p.y}`).join(' ')} 
                fill="none" 
                stroke="#a855f7" 
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              {drawingPath.map((p,i)=>(
                <circle key={i} cx={p.x} cy={p.y} r="3" fill="#a855f7" />
              ))}
            </svg>
          )}
        </div>
        </div>

        {/* RIGHT: Plan & Steps - only if not fullscreen */}
        {!isFullscreen && (
          <div className="w-full lg:w-[35%] flex flex-col min-h-0 border border-gray-800 rounded bg-gray-900/50 p-3 space-y-3">
            <div className="text-sm font-semibold text-gray-300 border-b border-gray-700 pb-2">Automation Plan</div>
            
            {/* Current Plan */}
            {planner.strategy ? (
              <div className="space-y-2">
                <div className="text-xs text-blue-400">Strategy: {planner.strategy}</div>
                <div className="text-xs text-gray-400">Steps: {planner.steps?.length || 0}</div>
                
                {/* Steps list */}
                <div className="max-h-64 overflow-y-auto space-y-1.5">
                  {(planner.steps || []).slice(0, 20).map((s:any, idx:number) => (
                    <div key={s.id || idx} className="p-2 bg-black/40 rounded text-xs">
                      <div className="flex items-start gap-2">
                        <span className="text-gray-500 flex-shrink-0">{idx+1}.</span>
                        <div className="flex-1">
                          <div className="text-gray-200">{s.action}</div>
                          {s.field && <div className="text-gray-400 text-[10px]">Field: {s.field}</div>}
                          {s.target && <div className="text-gray-400 text-[10px]">Target: {s.target}</div>}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-xs text-gray-500">No plan generated yet</div>
            )}
            
            {/* Saved Paths */}
            {savedPaths.length > 0 && (
              <div className="border-t border-gray-700 pt-3 space-y-2">
                <div className="text-xs font-semibold text-purple-400">Saved Paths ({savedPaths.length})</div>
                {savedPaths.map((path, idx)=>(
                  <div key={idx} className="p-2 bg-purple-900/20 border border-purple-700/50 rounded text-xs">
                    <div className="text-purple-300">{path.name}</div>
                    <div className="text-gray-400 text-[10px]">{path.path.length} points</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Bottom Tabs - only if not fullscreen */}
      {!isFullscreen && (
        <>
        {/* Tabs */}
        <div className="flex border-b border-gray-800 px-2 md:px-4 flex-shrink-0 overflow-x-auto">
          {['screen','detections','logs','chat'].map(tab=>(
            <button key={tab} onClick={()=>setActiveTab(tab as any)} className={`px-3 md:px-4 py-2 text-xs md:text-sm capitalize whitespace-nowrap ${activeTab===tab?'border-b-2 border-blue-500 text-blue-400':'text-gray-400 hover:text-gray-200'}`}>{tab}</button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto p-2 md:p-4 min-h-0">
          {activeTab==='screen' && (
            <div className="text-xs text-gray-400">
              <div>Session: <span className="text-gray-200">{sessionId || quickSessionId || '—'}</span></div>
              <div>URL: <span className="text-gray-200 text-xs">{observation?.url || '—'}</span></div>
              <div className="mt-2">Click on screen to select element, chat with AI below</div>
            </div>
          )}
          
          {activeTab==='detections' && (
            <div className="space-y-2">
              {vision.length===0 ? (
                <div className="text-gray-500 text-sm">No elements detected</div>
              ):(
                vision.map((v:any,i)=>(
                  <div key={i} onClick={()=>{setSelectedElement(v); setChatMessages(prev=>[...prev,{role:'system',text:`Selected: ${v.label||v.type}`}]);}} className={`p-2 border rounded text-xs cursor-pointer ${selectedElement===v?'border-blue-500 bg-blue-900/20':'border-gray-700 hover:border-gray-600'}`}>
                    <div className="text-gray-300">{v.label || v.type}</div>
                    <div className="text-gray-500">bbox: [{v.bbox.x},{v.bbox.y},{v.bbox.w},{v.bbox.h}] conf: {(v.confidence*100).toFixed(0)}%</div>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab==='logs' && (
            <div className="space-y-1 font-mono text-xs">
              {agentLogs.length===0 ? (
                <div className="text-gray-500">No logs yet</div>
              ):(
                agentLogs.map((log,i)=>(
                  <div key={i} className="text-gray-300">{log}</div>
                ))
              )}
            </div>
          )}

          {activeTab==='chat' && (
            <div className="flex flex-col h-full">
              {/* Instructions banner */}
              <div className="mb-3 p-3 bg-blue-900/20 border border-blue-700/50 rounded text-xs space-y-1">
                <div className="text-blue-300 font-semibold">💡 Manual Control:</div>
                <div className="text-gray-300">• Click element → selects it with number (#N)</div>
                <div className="text-gray-300">• <kbd className="px-1 bg-gray-700 rounded">Ctrl+Click</kbd> → sends click to browser</div>
                <div className="text-gray-300">• Type instructions like: "Click element #5" or "Type 'hello' in #3"</div>
              </div>
              
              <div className="flex-1 overflow-y-auto space-y-2 mb-4">
                {chatMessages.length===0 ? (
                  <div className="text-gray-500 text-sm">Start by clicking elements on screen or typing instructions.</div>
                ):(
                  chatMessages.map((msg,i)=>(
                    <div key={i} className={`p-2 rounded text-sm ${msg.role==='user'?'bg-blue-900/30 text-blue-100 ml-8':'bg-gray-800 text-gray-200 mr-8'}`}>
                      <div className="text-xs text-gray-400 mb-1">{msg.role}</div>
                      <div>{msg.text}</div>
                    </div>
                  ))
                )}
              </div>
              <div className="flex gap-2">
                <input value={chatInput} onChange={(e)=>setChatInput(e.target.value)} onKeyDown={(e)=>{if(e.key==='Enter'&&chatInput.trim()){setChatMessages(prev=>[...prev,{role:'user',text:chatInput}]); setChatInput(''); /* TODO: send to AI */}}} className="flex-1 px-3 py-2 bg-gray-900 border border-gray-700 rounded text-sm text-gray-200 placeholder-gray-500" placeholder="Type instruction for AI..." />
                <button onClick={()=>{if(chatInput.trim()){setChatMessages(prev=>[...prev,{role:'user',text:chatInput}]); setChatInput('');/* TODO: send to AI */}}} className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded text-white text-sm">Send</button>
              </div>
            </div>
          )}
        </div>
      </div>
      </>
      )}

    {/* Old layout removed */}
  </div>
  );
};

export default AutomationPage;

