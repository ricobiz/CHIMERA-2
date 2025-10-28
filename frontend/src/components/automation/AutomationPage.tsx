import React, { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import { PlayIcon, PauseIcon, StopIcon, BeakerIcon } from '../Icons';
const BASE_URL: string = (import.meta as any)?.env?.REACT_APP_BACKEND_URL || '';

type LogEntry = { ts: number; step: number; action: string; status?: 'ok'|'error'|'warning'|'info'; error?: string };

type Observation = {
  screenshot_base64?: string;
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
  // Quick test controls
  const [quickUrl, setQuickUrl] = useState<string>('https://google.com');
  const [quickSessionId, setQuickSessionId] = useState<string | null>(null);
  const [quickError, setQuickError] = useState<string | null>(null);

  // Freeze observation after manual Map/Smoke + persistent overlay payload
  const [freezeObsUntil, setFreezeObsUntil] = useState<number | null>(null);
  const [overlayVision, setOverlayVision] = useState<Observation['vision'] | null>(null);
  const [overlayViewport, setOverlayViewport] = useState<Observation['viewport'] | null>(null);
  const [overlayGrid, setOverlayGrid] = useState<Observation['grid'] | null>(null);

  // Detection overlay controls
  const [showDetections, setShowDetections] = useState<boolean>(true);
  const [zoomEnabled, setZoomEnabled] = useState<boolean>(false);

  const viewerRef = useRef<HTMLDivElement | null>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const overlayRef = useRef<HTMLDivElement | null>(null);
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
    setOverlayRect({ left: iRect.left - vRect.left, top: iRect.top - vRect.top, width: iRect.width, height: iRect.height });
  }, []);

  useEffect(() => {
    updateOverlayRect();
    const fn = () => updateOverlayRect();
    window.addEventListener('resize', fn);
    const intv = setInterval(fn, 1000);
    return () => { window.removeEventListener('resize', fn); clearInterval(intv); };
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
      // If freeze window active, do not overwrite overlays (keeps detections visible)
      if (!freezeObsUntil || Date.now() > freezeObsUntil) {
        setObservation(data.observation || null);
        setOverlayVision(data.observation?.vision || null);
        setOverlayViewport(data.observation?.viewport || null);
        setOverlayGrid(data.observation?.grid || null);
      }
      setSessionId(data.session_id || null);
      if (data.ask_user) setAskUser(data.ask_user); else setAskUser(null);
      if (data.profile_id) setProfileId(data.profile_id);
      if (data.observation?.screenshot_base64) setPendingSrc(data.observation.screenshot_base64);
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

  // Unfreeze observation after timeout (top-level effect)
  useEffect(() => {
    if (!freezeObsUntil) return;
    const t = setInterval(() => {
      if (Date.now() > freezeObsUntil) setFreezeObsUntil(null);
    }, 250);
    return () => clearInterval(t);
  }, [freezeObsUntil]);

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
      let sid = quickSessionId;
      if (!sid) {
        // Auto-create a session if none exists
        const newId = 'auto-' + Date.now();
        const respCreate = await fetch(`${BASE_URL}/api/automation/session/create`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: newId, use_proxy: false }) });
        const dataCreate = await respCreate.json();
        if (!respCreate.ok || !dataCreate.session_id) throw new Error(dataCreate.detail || 'create failed');
        sid = dataCreate.session_id;
        setQuickSessionId(sid);
      }
      const resp = await fetch(`${BASE_URL}/api/automation/navigate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sid, url: quickUrl }) });
      const data = await resp.json();
      if (!resp.ok || data.success === false) throw new Error(data.error || data.detail || 'navigate failed');
      const shot = await fetch(`${BASE_URL}/api/automation/screenshot?session_id=${encodeURIComponent(sid)}`);
      const js = await shot.json();
      if (js.screenshot_base64) {
        setPendingSrc(js.screenshot_base64);
        setObservation(js);
        // persist overlays irrespective of polling
        setOverlayVision(js.vision || []);
        setOverlayViewport(js.viewport || null);
        setOverlayGrid(js.grid || null);
        setShowDetections(true);
        setFreezeObsUntil(Date.now() + 5000); // freeze 5s so overlays stay visible
      } else setQuickError('No screenshot returned');
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

  // Click handler on the screenshot to show calculated cell
  const handleImageClick = (e: React.MouseEvent<HTMLImageElement>) => {
    const img = imageRef.current;
    const view = viewerRef.current;
    if (!img || !view || !overlayRect) return;
    const vRect = view.getBoundingClientRect();
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
    // auto hide lens label
    setTimeout(() => setTapCell(null), 1200);
  };

  // Overlay: show first N vision detections
  const renderDetections = () => {
    if (!showDetections) return null;
    const v = (overlayVision ?? observation?.vision) || [];
    const rows = parseInt(((overlayGrid ?? observation?.grid)?.rows as any) || (gridPreset.split('x')[1] as any) || '32', 10);
    const cols = parseInt(((overlayGrid ?? observation?.grid)?.cols as any) || (gridPreset.split('x')[0] as any) || '48', 10);
    // only show top 20 to avoid clutter
    return (v.slice(0, 20).map((el, idx) => {
      const { colIdx, rowIdx } = parseCell(el.cell as string);
      const left = ((colIdx + 0.5) / cols) * 100;
      const top = ((rowIdx + 0.5) / rows) * 100;
      return (
        <div key={idx} className="absolute" style={{ left: `${left}%`, top: `${top}%`, transform: 'translate(-50%, -50%)' }}>
          <div className="px-1.5 py-0.5 text-[9px] rounded bg-blue-900/70 border border-blue-500 text-blue-100 whitespace-nowrap max-w-[160px] overflow-hidden text-ellipsis">{el.label || el.type} · {el.cell}</div>
        </div>
      );
    }));
  };

  // BBox overlay using viewport scaling
  const renderBBoxes = () => {
    if (!showDetections) return null;
    const v = observation?.vision || [];
    const vw = observation?.viewport?.width || 1280;
    const vh = observation?.viewport?.height || 800;
    if (!overlayRect) return null;
    return v.slice(0, 20).map((el, idx) => {
      const b = el.bbox || ({} as any);
      const x = (b.x || 0) * overlayRect.width / vw;
      const y = (b.y || 0) * overlayRect.height / vh;
      const w = (b.w || 0) * overlayRect.width / vw;
      const h = (b.h || 0) * overlayRect.height / vh;
      return (
        <div key={`bb-${idx}`} className="absolute border-2 border-pink-400/90 shadow-[0_0_4px_rgba(255,0,128,0.7)]" style={{ left: `${overlayRect.left + x}px`, top: `${overlayRect.top + y}px`, width: `${w}px`, height: `${h}px` }} />
      );
    });
  };

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
          </div>
          {/* Icon controls + compact grid */}
          <div className="flex items-center gap-1 flex-wrap justify-end">
            <button title="Play" onClick={() => control('ACTIVE')} className="p-2 rounded bg-gray-800/70 hover:bg-gray-700/70 border border-gray-700 text-green-300"><PlayIcon className="w-4 h-4"/></button>
            <button title="Pause" onClick={() => control('PAUSED')} className="p-2 rounded bg-gray-800/70 hover:bg-gray-700/70 border border-gray-700 text-yellow-300"><PauseIcon className="w-4 h-4"/></button>
            <button title="Stop" onClick={() => control('STOP')} className="p-2 rounded bg-gray-800/70 hover:bg-gray-700/70 border border-gray-700 text-red-300"><StopIcon className="w-4 h-4"/></button>
            <span className={`text-[10px] px-1.5 py-0.5 rounded ${statusPill(agentStatus)}`}>{agentStatus}</span>
            <label className="text-[10px] text-gray-400 hidden sm:block">Grid</label>
            <select value={gridPreset} onChange={async (e:any)=>{
              const v = e.target.value as typeof gridPreset;
              setGridPreset(v);
              const [cols, rows] = v.split('x').map((n)=>parseInt(n,10));
              try { await fetch(`${BASE_URL}/api/automation/grid/set`, { method: 'POST', headers: { 'Content-Type':'application/json' }, body: JSON.stringify({ rows, cols }) }); } catch {}
            }} className="px-1.5 py-1 text-[11px] bg-gray-800/60 border border-gray-700 rounded text-gray-300 w-24">
              <option value="8x6">8×6</option>
              <option value="12x8">12×8</option>
              <option value="16x12">16×12</option>
              <option value="24x16">24×16</option>
              <option value="32x24">32×24</option>
              <option value="48x32">48×32</option>
              <option value="64x48">64×48</option>
            </select>
            <button onClick={() => setShowGrid(s => !s)} className="px-2 py-1 text-[11px] bg-gray-800/60 hover:bg-gray-700/60 border border-gray-700 rounded text-gray-300">{showGrid ? 'Hide' : 'Show'}</button>
            <button onClick={() => setZoomEnabled(z => !z)} className={`px-2 py-1 text-[11px] border rounded ${zoomEnabled? 'bg-blue-900/40 border-blue-700 text-blue-300' : 'bg-gray-800/60 border-gray-700 text-gray-300'}`}>Zoom</button>
            <button onClick={() => setShowDetections(v => !v)} className={`px-2 py-1 text-[11px] border rounded ${showDetections? 'bg-green-900/30 border-green-700 text-green-300' : 'bg-gray-800/60 border-gray-700 text-gray-300'}`}>Detections</button>
            <button onClick={quickNavigate} className="px-2 py-1 text-[11px] bg-blue-800/60 hover:bg-blue-700/60 border border-blue-700 rounded text-blue-300">Map</button>
            <button onClick={() => setShowFullscreen(true)} className="px-2 py-1 text-[11px] bg-gray-800/60 hover:bg-gray-700/60 border border-gray-700 rounded text-gray-300">Full</button>
          </div>
        </div>
      </div>

      {/* Top: Live Viewer */}
      <div className="px-4 md:px-6 py-3 md:py-4 border-b border-gray-800 flex-shrink-0">
        <div ref={viewerRef} className="relative w-full h-72 md:h-[420px] border border-gray-800 rounded bg-black/60 overflow-hidden flex items-center justify-center">
          {quickError && (
            <div className="absolute top-2 left-2 right-2 text-[11px] text-red-300 bg-red-900/30 border border-red-800 rounded px-2 py-1">{quickError}</div>
          )}

          {displaySrc ? (
            <img ref={imageRef} onLoad={updateOverlayRect} onClick={handleImageClick} src={`data:image/png;base64,${displaySrc}`} alt="screenshot" className="max-w-full max-h-full object-contain cursor-crosshair select-none" />
          ) : (
            <div className="text-xs text-gray-600">No screenshot</div>
          )}

          {/* Grid overlay aligned to image rect */}
          {showGrid && overlayRect && (
            <div ref={overlayRef} className="absolute pointer-events-none" style={{ left: overlayRect.left, top: overlayRect.top, width: overlayRect.width, height: overlayRect.height }}>
              <div className="w-full h-full" style={{ backgroundImage: `linear-gradient(rgba(200,200,200,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(200,200,200,0.08) 1px, transparent 1px)`, backgroundSize: `${overlayRect.width/parseInt(gridPreset.split('x')[0],10)}px ${overlayRect.height/parseInt(gridPreset.split('x')[1],10)}px` }} />
            </div>
          )}

          {tapCell && overlayRect && (
            <div className="absolute" style={{ left: `${overlayRect.left + (tapCell.left/100)*overlayRect.width}px`, top: `${overlayRect.top + (tapCell.top/100)*overlayRect.height}px`, transform: 'translate(-50%, -50%)' }}>
              <div className="px-1.5 py-0.5 text-[10px] rounded bg-black/80 border border-gray-600 text-gray-100">{tapCell.cell}</div>
            </div>
          )}

          {/* Detected elements overlay (labels + bboxes) */}
          {overlayRect && (
            <div className="absolute inset-0 pointer-events-none" style={{ left: overlayRect.left, top: overlayRect.top, width: overlayRect.width, height: overlayRect.height }}>
              {renderDetections()}
            </div>
          )}
          {renderBBoxes()}

          {ghostCell && overlayRect && (
            <div className="absolute transition-all duration-300" style={{ left: `${overlayRect.left + (ghostPos.left/100)*overlayRect.width}px`, top: `${overlayRect.top + (ghostPos.top/100)*overlayRect.height}px`, transform: 'translate(-50%, -50%)' }}>
              <div className="w-4 h-4 rounded-full bg-white/90 shadow-[0_0_10px_rgba(255,255,255,0.6)] border border-gray-200" />
            </div>
          )}
        </div>

        {/* URL + actions under viewer */}
        <div className="mt-3">
          <input value={quickUrl} onChange={(e:any)=>setQuickUrl(e.target.value)} className="w-full px-3 py-2 text-[12px] bg-black/60 border border-gray-700 rounded text-gray-200 placeholder-gray-500" placeholder="https://..." />
          <div className="mt-2 grid grid-cols-2 gap-2">
            <button onClick={quickNavigate} className="px-2 py-2 text-[12px] bg-blue-800/70 hover:bg-blue-700/70 border border-blue-700 rounded text-blue-200 flex items-center justify-center gap-1"><span>Go</span></button>
            <button onClick={async()=>{ try{ const resp = await fetch(`${BASE_URL}/api/automation/smoke-check`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ url: quickUrl, use_proxy:false }) }); const data = await resp.json(); if (data?.screenshot_base64) { setPendingSrc(data.screenshot_base64); setObservation(data); setShowDetections(true);} } catch(e:any){ alert(e.message||'Smoke failed');}}} className="px-2 py-2 text-[12px] bg-green-800/70 hover:bg-green-700/70 border border-green-700 rounded text-green-200 flex items-center justify-center gap-1"><BeakerIcon className="w-4 h-4"/><span>Smoke</span></button>
          </div>
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
              <button onClick={() => control('PAUSED')} className="px-3 py-1.5 bg-yellow-600/20 hover:bg-yellow-600/30 border border-yellow-600/50 text-yellow-400 rounded text-xs">Pause</button>
              <button onClick={() => control('STOP')} className="px-3 py-1.5 bg-red-600/20 hover:bg-red-600/30 border border-red-600/50 text-red-400 rounded text-xs">Stop</button>
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
            <button onClick={startTask} disabled={isSubmitting || !taskText.trim()} className="mt-3 w-full px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all">{isSubmitting ? 'Starting...' : 'Run Task'}</button>
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
