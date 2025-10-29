import React, { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import { PlayIcon, PauseIcon, StopIcon, BeakerIcon } from '../Icons';
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

const AutomationPage: React.FC<{ onClose?: () => void }> = ({ onClose }) => {
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
        setAgentStatus('ACTIVE');
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
      setIsExecuting(false);
      setIsSubmitting(false);
      setIsWarming(false);
      setWarmupProgress('');
      setExecutionSubtitle('');
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
      // Use smoke-check for atomic navigate+screenshot+vision
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
    <div className="flex flex-col bg-[#0f0f10] text-gray-100 overflow-x-hidden" style={{ height: '100dvh' }}>
      {/* Header */}
      <div className="px-3 md:px-4 py-2 border-b border-gray-800 flex-shrink-0 bg-[#0f0f10] sticky top-0 z-10">
        <div className="flex items-center justify-between gap-2 min-w-0">
          <div className="flex items-center gap-2 min-w-0">
            {onClose && (
              <button onClick={onClose} className="px-2 py-1 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors flex items-center gap-1 text-[12px]">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
                Back
              </button>
            )}
            <div className="truncate text-[12px] md:text-sm text-gray-300">Browser Automation</div>
          {/* Lens controls removed for stability */}

          </div>
          {/* URL row moved to header */}
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <input value={quickUrl} onChange={(e:any)=>setQuickUrl(e.target.value)} className="w-full px-3 py-1.5 text-[12px] bg-black/40 border border-gray-700 rounded text-gray-200 placeholder-gray-500" placeholder="https://..." />
            <button title="Run" onClick={quickNavigate} className="p-2 rounded bg-blue-800/70 hover:bg-blue-700/70 border border-blue-700 text-blue-200"><PlayIcon className="w-4 h-4"/></button>
            <span className={`text-[10px] px-1.5 py-0.5 rounded ${statusPill(agentStatus)}`}>{agentStatus}</span>
          </div>
          {/* Side icon strips */}
          {/* Side icon strips */}
          {/* Side icons removed for compact bottom toolbar */}

            {/* removed legacy top icon strips and buttons; all controls moved to bottom toolbar */}
          </div>
        </div>

      <div className="px-4 md:px-6 py-3 md:py-4 border-b border-gray-800 flex-shrink-0">
        <div ref={viewerRef} className="relative w-full h-72 md:h-[520px] border border-gray-800 rounded bg-black/60 overflow-hidden flex items-center justify-center" style={{ touchAction: 'none', overscrollBehavior: 'contain' }}>
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
            <canvas ref={canvasRef} className="absolute pointer-events-none" style={{ left: overlayRect.left, top: overlayRect.top, width: overlayRect.width, height: overlayRect.height }} />
          )}

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
        </div>

        {/* Bottom toolbar - все кнопки в один ряд ПОД viewer'ом */}
        <div className="mt-3 flex flex-wrap items-center justify-center gap-2">
          {/* Existing buttons */}
          <button onClick={quickNavigate} className="px-3 py-1.5 text-xs bg-blue-900/70 hover:bg-blue-800/70 border border-blue-800 rounded text-blue-200">Map</button>
          <button onClick={()=> setPinMapping(p => !p)} className={`px-3 py-1.5 text-xs border rounded ${pinMapping? 'bg-teal-900/40 border-teal-700 text-teal-300' : 'bg-gray-900/70 border-gray-700 text-gray-200'}`}>{pinMapping? 'Pinned' : 'Pin'}</button>
          <button onClick={()=>{ lastSnapshotRef.current=null; setVision([]); drawCanvas(); }} className="px-3 py-1.5 text-xs bg-gray-900/70 hover:bg-gray-800/70 border border-gray-700 rounded text-gray-200">Clear</button>
          <button onClick={()=> setShowDetections(v=>!v)} className="px-3 py-1.5 text-xs bg-gray-900/70 hover:bg-gray-800/70 border border-gray-700 rounded text-gray-200">{showDetections? 'Hide' : 'Show'}</button>
          <button onClick={()=> setShowGrid(s=>!s)} className="px-3 py-1.5 text-xs bg-gray-900/70 hover:bg-gray-800/70 border border-gray-700 rounded text-gray-200">Grid</button>
          <button onClick={()=> setShowPlan(v=>!v)} className="px-3 py-1.5 text-xs bg-gray-900/70 hover:bg-gray-800/70 border border-gray-700 rounded text-gray-200">Plan</button>
          <button onClick={async()=>{ const url = prompt('Введите URL для входа', quickUrl) || quickUrl; setQuickUrl(url); await quickNavigate(); }} className="px-3 py-1.5 text-xs bg-blue-900/70 hover:bg-blue-800/70 border border-blue-800 rounded text-blue-200">Открыть URL</button>
          <button onClick={async()=>{ if (!sessionId) { alert('Сессия не активна'); return; } try { const resp = await fetch(`${BASE_URL}/api/profile/save_from_session`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ session_id: sessionId }) }); const d = await resp.json(); if (d?.profile_id) alert('Профиль сохранён и прогрет'); else alert('Не удалось сохранить профиль'); } catch(e:any){ alert(e.message||'Ошибка сохранения профиля'); } }} className="px-3 py-1.5 text-xs bg-emerald-900/70 hover:bg-emerald-800/70 border border-emerald-800 rounded text-emerald-200">Сохранить</button>
        </div>

      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto flex flex-col lg:flex-row gap-4 p-4 md:p-6">
        {/* Left Column */}
        <div className="lg:w-1/3 space-y-4">
          {/* Controls (desktop) */}
          <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4 hidden md:block">
            <div className="text-sm text-gray-400 font-medium mb-2">Controls</div>
            <div className="flex gap-2">
              <button onClick={() => control('ACTIVE')} className="px-3 py-1.5 bg-green-600/20 hover:bg-green-600/30 border border-green-600/50 text-green-400 rounded text-xs">Resume</button>
          {/* Adjust mini-chat under viewer */}
          <div className="mt-2 flex items-center gap-2">
            <input value={adjustMsg} onChange={e=> setAdjustMsg(e.target.value)} placeholder="Подсказать плану (корректировки)..." className="flex-1 px-2 py-1 bg-gray-900/70 border border-gray-700 rounded text-[12px]" />
            <button onClick={async()=>{
              if(!adjustMsg.trim()) return;
              try{
                await fetch(`${BASE_URL}/api/hook/adjust`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ message: adjustMsg })});
                setAdjustMsg('');
              }catch(e:any){ alert(e.message||'Ошибка отправки'); }
            }} className="px-2 py-1 bg-indigo-800 hover:bg-indigo-700 border border-indigo-700 rounded text-[12px]">Отправить</button>
          </div>

              <button onClick={() => control('PAUSED')} className="px-3 py-1.5 bg-yellow-600/20 hover:bg-yellow-600/30 border border-yellow-600/50 text-yellow-400 rounded text-xs">Pause</button>
              <button onClick={() => control('STOP')} className="px-3 py-1.5 bg-red-600/20 hover:bg-red-600/30 border border-red-600/50 text-red-400 rounded text-xs">Stop</button>
            </div>
          </div>

          {/* Detections list */}
          <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400 font-medium">Detections ({currentDetections.length})</span>
              <div className="flex items-center gap-2">
                <label className="text-[10px] text-gray-500">Show</label>
                <input type="checkbox" checked={showDetections} onChange={(e)=>{ if (!e.target.checked) { const cvs = canvasRef.current; if (cvs && overlayRect) { const ctx = cvs.getContext('2d'); if (ctx) { ctx.clearRect(0,0,overlayRect.width, overlayRect.height); } } } setShowDetections(e.target.checked); }} />
              </div>
            </div>
            <div className="max-h-48 overflow-y-auto space-y-1">
              {currentDetections.slice(0,30).map((el, idx) => (
                <div key={idx} className="text-[11px] text-gray-300 flex items-center gap-2">
                  <span className="text-gray-500">{el.cell || '—'}</span>
                  <span className="flex-1 truncate">{el.label || el.type}</span>
                </div>
              ))}
              {currentDetections.length === 0 && (
                <div className="text-[11px] text-gray-600">No detections yet. Press Map.</div>
              )}
            </div>
          </div>

          {/* Step Timeline */}
          <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-gray-400 font-medium">Step Timeline</span>
              <div className="flex items-center gap-2 flex-wrap">
                <label className="text-[10px] text-gray-500">Auto-scroll</label>
                <input type="checkbox" checked={autoScrollLogs && !userReadingLogs} onChange={(e)=> setAutoScrollLogs(e.target.checked)} />
              </div>
            </div>
            <div className="max-h-64 overflow-y-auto space-y-1" onMouseEnter={()=> setUserReadingLogs(true)} onMouseLeave={()=> setUserReadingLogs(false)} onTouchStart={()=> setUserReadingLogs(true)} onTouchEnd={()=> setUserReadingLogs(false)}>
              {(logs || []).map((l, idx) => (
                <div key={idx} className="text-xs text-gray-300 flex items-center gap-2">
                  <span className="text-gray-500 w-16">Step {l.step}</span>
                  <span className="flex-1 truncate">{l.action}</span>
                  <span className={`w-12 text-right ${l.status==='ok'?'text-green-400':l.status==='error'?'text-red-400':'text-gray-400'}`}>{l.status || ''}</span>
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          </div>

          {/* Profile Health */}
          <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-gray-400 font-medium">Profile Health</span>
              <button onClick={recheckProfile} className="px-3 py-1.5 bg-purple-600/20 hover:bg-purple-600/30 border border-purple-600/50 text-purple-300 rounded text-xs">Re-check</button>
            </div>
            <div className="text-xs text-gray-400 space-y-1">
              <div>profile_id: <span className="text-gray-200">{profileId || '—'}</span></div>
              <div>warm: <span className="text-gray-200">{profileWarm ? 'yes' : 'no'}</span></div>
              <div>clean: <span className="text-gray-200">{profileClean === null ? '—' : profileClean ? '✅' : '❌'}</span></div>
            </div>
          </div>

          {/* Task Input */}
          <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4">
            <label className="block text-sm text-gray-400 font-medium mb-2">Task</label>
            <textarea className="w-full h-24 bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-blue-500 resize-none" value={taskText} onChange={(e) => setTaskText(e.target.value)} />
            <div className="mt-3 flex gap-2">
              <button onClick={startTask} disabled={isSubmitting || !taskText.trim()} className="flex-1 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all">{isSubmitting ? 'Starting...' : '▶️ Run Task'}</button>
              <button onClick={resetTask} className="px-4 py-2 bg-red-600/80 hover:bg-red-500/80 text-white rounded-lg font-semibold transition-all" title="Сбросить задачу и очистить всё">🔄 Сброс</button>
            </div>
          </div>
        </div>

        {/* Right Column: Execution Logs Raw */}
        <div className="lg:w-2/3">
          <div className="bg-black border border-gray-800 rounded-lg h-full flex flex-col">
            <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm text-green-400 font-mono">EXECUTION LOG</span>
              </div>
              <span className="text-xs text-gray-600">{logs.length} entries</span>
            </div>
            <div className="flex-1 overflow-y-auto p-4 font-mono text-sm">
              {logs.length === 0 ? (
                <div className="text-gray-600 text-center py-12">No logs yet. Run a task to see execution steps...</div>
              ) : (
                <div className="space-y-1">
                  {logs.map((log, idx) => (
                    <div key={idx} className={`flex gap-3 ${log.status === 'error' ? 'text-red-400' : log.status === 'warning' ? 'text-yellow-400' : log.status === 'ok' ? 'text-green-400' : 'text-gray-400' }`}>
                      <span className="text-gray-600">[{new Date(log.ts).toLocaleTimeString()}]</span>
                      <span className="text-gray-500">Step {log.step}:</span>
                      <span>{log.action}</span>
                      {log.error && (<span className="text-red-500">→ ERROR: {log.error}</span>)}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Fullscreen modal */}
      {showFullscreen && (
        <div className="fixed inset-0 bg-black/90 z-[100] p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="text-sm text-gray-400">Fullscreen Viewer</div>
            <button onClick={() => setShowFullscreen(false)} className="px-3 py-1 text-xs bg-gray-800/60 hover:bg-gray-700/60 border border-gray-700 rounded text-gray-300">Close</button>
          </div>
          <div className="w-full h-[calc(100%-40px)] border border-gray-800 rounded bg-black flex items-center justify-center">
            {displaySrc ? (
              <img src={`data:image/png;base64,${displaySrc}`} alt="screenshot-full" className="max-w-full max-h-full object-contain" />
            ) : (
              <div className="text-xs text-gray-600">No screenshot</div>
            )}
          </div>
        </div>
      )}

      {/* Waiting User modal */}
      {askUser && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-[#0f0f10] border border-gray-800 rounded-lg w-full max-w-md p-4">
            <div className="text-sm text-gray-300 mb-2">Agent needs your input</div>
            <div className="text-xs text-gray-400 mb-3">{askUser}</div>
            <div className="flex items-center gap-2 flex-wrap">
              <input id="user_input_field" className="flex-1 px-2 py-1 text-xs bg-gray-900 border border-gray-700 rounded text-gray-300" placeholder="Enter value (phone/code)" />
              <button onClick={async() => { const val = (document.getElementById('user_input_field') as HTMLInputElement).value; if (!jobId) return; await fetch(`${BASE_URL}/api/hook/user_input`, { method: 'POST', headers: { 'Content-Type':'application/json' }, body: JSON.stringify({ job_id: jobId, field: 'code', value: val })}); setAskUser(null); }} className="px-3 py-1.5 text-xs bg-blue-600/20 hover:bg-blue-600/30 border border-blue-600/50 text-blue-300 rounded">Submit</button>
              <button onClick={() => setAskUser(null)} className="px-3 py-1.5 text-xs bg-gray-800/20 hover:bg-gray-800/30 border border-gray-700 text-gray-300 rounded">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AutomationPage;
