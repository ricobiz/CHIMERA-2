import React, { useEffect, useMemo, useRef, useState } from 'react';

import { useCallback } from 'react';
const BASE_URL: string = (import.meta as any)?.env?.REACT_APP_BACKEND_URL || '';

type LogEntry = { ts: number; step: number; action: string; status?: 'ok'|'error'|'warning'|'info'; error?: string };

type Observation = {
  screenshot_base64?: string;
  grid?: { rows: number; cols: number };
  vision?: Array<{ cell: string; label: string; type: string; confidence: number }>;
  status?: string;
  url?: string;
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
  const [gridPreset, setGridPreset] = useState<'8x6'|'12x8'|'16x12'|'24x16'|'32x24'>('24x16');
  const [showFullscreen, setShowFullscreen] = useState<boolean>(false);
  const [displaySrc, setDisplaySrc] = useState<string | null>(null);
  const [pendingSrc, setPendingSrc] = useState<string | null>(null);
  // Quick test controls
  const [quickUrl, setQuickUrl] = useState<string>('https://example.com');
  const [quickSessionId, setQuickSessionId] = useState<string | null>(null);
  const [quickError, setQuickError] = useState<string | null>(null);

  const viewerRef = useRef<HTMLDivElement | null>(null);
  const logsEndRef = useRef<HTMLDivElement | null>(null);
  const pollRef = useRef<any>(null);

  // Smooth screenshot swapping
  useEffect(() => {
    if (!pendingSrc) return;
    const img = new Image();
    img.onload = () => setDisplaySrc(pendingSrc);
    img.src = `data:image/png;base64,${pendingSrc}`;
  }, [pendingSrc]);

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
      setObservation(data.observation || null);
      setSessionId(data.session_id || null);
      if (data.ask_user) setAskUser(data.ask_user); else setAskUser(null);
      if (data.profile_id) setProfileId(data.profile_id);
      if (data.observation?.screenshot_base64) setPendingSrc(data.observation.screenshot_base64);
    } catch (e) {
      // silent
    }
  };
    // Sync initial grid preset from backend
    (async()=>{ try { const r = await fetch(`${BASE_URL}/api/automation/grid`); const js = await r.json(); const v = `${js.cols || 16}x${js.rows || 24}` as any; setGridPreset((['8x6','12x8','16x12','24x16','32x24'] as any).includes(v)? v: '24x16'); } catch {} })();

  useEffect(() => {
    pollRef.current = setInterval(loadLogs, 1500);
    return () => clearInterval(pollRef.current);
  }, []);

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
    const match = step?.action?.match(/[A-H][0-9]{1,2}/)?.[0];
    return match || null;
  }, [logs]);

  const cellToPercent = (cell: string | null, grid?: {rows:number; cols:number}) => {
    if (!cell || !grid) return { left: 50, top: 50 };
    const colLetter = cell[0].toUpperCase();
    const rowNum = parseInt(cell.slice(1), 10);
    const colIndex = colLetter.charCodeAt(0) - 'A'.charCodeAt(0);
    const rowIndex = rowNum - 1;
    const left = ((colIndex + 0.5) / (grid.cols || 8)) * 100;
    const top = ((rowIndex + 0.5) / (grid.rows || 12)) * 100;
    return { left, top };
  };

  // Quick test: create session, navigate and screenshot
  const quickCreate = async () => {
    try {
      const sid = 'auto-' + Date.now();
      setQuickError(null);
      const resp = await fetch(`${BASE_URL}/api/automation/session/create`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sid, use_proxy: false }) });
      const data = await resp.json();
      if (!resp.ok || !data.session_id) throw new Error(data.detail || 'create failed');
      setQuickSessionId(data.session_id || sid);
    } catch (e: any) {
      alert(e.message || 'Quick create failed');
    }
  };

  const quickNavigate = async () => {
    if (!quickSessionId) return alert('Create session first');
    try {
      setQuickError(null);
      const resp = await fetch(`${BASE_URL}/api/automation/navigate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: quickSessionId, url: quickUrl }) });
      const data = await resp.json();
      if (!resp.ok || data.success === false) throw new Error(data.error || data.detail || 'navigate failed');
      const shot = await fetch(`${BASE_URL}/api/automation/screenshot?session_id=${encodeURIComponent(quickSessionId)}`);
      const js = await shot.json();
      if (js.screenshot_base64) setPendingSrc(js.screenshot_base64);
      else setQuickError('No screenshot returned');
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

  return (
    <div className="flex flex-col bg-[#0f0f10] text-gray-100 overflow-x-hidden" style={{ height: '100dvh' }}>
      {/* Header */}
      <div className="px-4 md:px-6 py-3 md:py-4 border-b border-gray-800 flex-shrink-0 bg-[#0f0f10] sticky top-0 z-10">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {onClose && (
              <button onClick={onClose} className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors flex items-center gap-2 text-sm">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
                Back
              </button>
            )}
            <div>
              <h1 className="text-xl md:text-2xl font-bold text-white">Browser Automation</h1>
              <p className="text-xs md:text-sm text-gray-400">Agent live view, steps and controls</p>
            </div>
            <span className={`text-[10px] px-2 py-0.5 rounded ${agentStatus==='ERROR'?'bg-red-900/40 text-red-300': agentStatus==='ACTIVE'?'bg-green-900/40 text-green-300': 'bg-gray-900/40 text-gray-300'}`}>{agentStatus}</span>
          <div className="flex items-center gap-2">
            <label className="text-[10px] text-gray-400">Grid</label>
          {/* Compact controls row for mobile */}
          <div className="absolute bottom-1 left-2 right-2 flex items-center gap-2 z-10 md:hidden">
            <button onClick={quickCreate} className="flex-1 px-2 py-1 text-[11px] bg-gray-800/70 hover:bg-gray-700/70 border border-gray-700 rounded text-gray-200">Create</button>
            <button onClick={quickNavigate} className="flex-1 px-2 py-1 text-[11px] bg-blue-800/70 hover:bg-blue-700/70 border border-blue-700 rounded text-blue-200">Go</button>
            <button onClick={async()=>{
              try {
                const resp = await fetch(`${BASE_URL}/api/automation/smoke-check`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url: quickUrl, use_proxy: false }) });
                const data = await resp.json();
                if (data?.screenshot_base64) setPendingSrc(data.screenshot_base64);
              } catch (e:any) { alert(e.message || 'Smoke-check failed'); }
            }} className="px-2 py-1 text-[11px] bg-green-800/70 hover:bg-green-700/70 border border-green-700 rounded text-green-200">Smoke</button>
          </div>
            <select value={gridPreset} onChange={async (e:any)=>{
              const v = e.target.value as typeof gridPreset;
              setGridPreset(v);
              const [cols, rows] = v.split('x').map((n)=>parseInt(n,10));
              try {
                await fetch(`${BASE_URL}/api/automation/grid/set`, { method: 'POST', headers: { 'Content-Type':'application/json' }, body: JSON.stringify({ rows, cols }) });
              } catch {}
            }} className="px-2 py-1 text-xs bg-gray-800/60 border border-gray-700 rounded text-gray-300">
              <option value="8x6">8×6</option>
              <option value="12x8">12×8</option>
              <option value="16x12">16×12</option>
              <option value="24x16">24×16</option>
              <option value="32x24">32×24</option>
            <button onClick={async()=>{
              try {
                const resp = await fetch(`${BASE_URL}/api/automation/smoke-check`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url: quickUrl, use_proxy: false }) });
                const data = await resp.json();
                if (data?.screenshot_base64) {
                  setPendingSrc(data.screenshot_base64);
                }
              } catch (e:any) { alert(e.message || 'Smoke-check failed'); }
            }} className="px-2 py-1 text-xs bg-green-800/60 hover:bg-green-700/60 border border-green-700 rounded text-green-300">Smoke</button>
            </select>
          </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={`text-[10px] px-2 py-0.5 rounded ${statusPill(agentStatus)}`}>{agentStatus}</span>
            <button onClick={() => setShowGrid(s => !s)} className="px-2 py-1 text-xs bg-gray-800/60 hover:bg-gray-700/60 border border-gray-700 rounded text-gray-300">{showGrid ? 'Hide Grid' : 'Show Grid'}</button>
            <button onClick={() => setShowFullscreen(true)} className="px-2 py-1 text-xs bg-gray-800/60 hover:bg-gray-700/60 border border-gray-700 rounded text-gray-300">Fullscreen</button>
          </div>
        </div>
      </div>

      {/* Top: Live Viewer */}
      <div className="px-4 md:px-6 py-3 md:py-4 border-b border-gray-800 flex-shrink-0">
        <div className="relative w-full h-72 md:h-[420px] border border-gray-800 rounded bg-black/60 overflow-hidden flex items-center justify-center pb-8">
          {/* Quick test controls */}
          <div className="absolute top-2 left-2 right-2 hidden md:flex items-center gap-2 z-10">
            <input value={quickUrl} onChange={(e:any)=>setQuickUrl(e.target.value)} className="flex-1 px-2 py-1 text-xs bg-black/60 border border-gray-700 rounded text-gray-200 placeholder-gray-500" placeholder="https://..." />
            <button onClick={quickCreate} className="px-2 py-1 text-xs bg-gray-800/60 hover:bg-gray-700/60 border border-gray-700 rounded text-gray-300">Create</button>
            <button onClick={quickNavigate} className="px-2 py-1 text-xs bg-blue-800/60 hover:bg-blue-700/60 border border-blue-700 rounded text-blue-300">Go</button>
            <button onClick={async()=>{
              try {
                const resp = await fetch(`${BASE_URL}/api/automation/smoke-check`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url: quickUrl, use_proxy: false }) });
                const data = await resp.json();
                if (data?.screenshot_base64) setPendingSrc(data.screenshot_base64);
              } catch (e:any) { alert(e.message || 'Smoke-check failed'); }
            }} className="px-2 py-1 text-xs bg-green-800/60 hover:bg-green-700/60 border border-green-700 rounded text-green-300">Smoke</button>
          </div>

        {quickError && (
          <div className="absolute bottom-2 left-2 right-2 text-[11px] text-red-300 bg-red-900/30 border border-red-800 rounded px-2 py-1">{quickError}</div>
        )}

          {displaySrc ? (
            <img src={`data:image/png;base64,${displaySrc}`} alt="screenshot" className="max-w-full max-h-full object-contain" />
          ) : (
            <div className="text-xs text-gray-600">No screenshot</div>
          )}
          {showGrid && (
            <div className="absolute inset-0 pointer-events-none">
              <div className="w-full h-full" style={{ backgroundImage: `linear-gradient(rgba(200,200,200,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(200,200,200,0.08) 1px, transparent 1px)`, backgroundSize: `${(100/((gridPreset.split('x')[0] as any)|0 || 16))}% ${(100/((gridPreset.split('x')[1] as any)|0 || 24))}%` }} />
            </div>
          )}
          {ghostCell && (
            <div className="absolute transition-all duration-300" style={{ left: `${ghostPos.left}%`, top: `${ghostPos.top}%`, transform: 'translate(-50%, -50%)' }}>
              <div className="w-4 h-4 rounded-full bg-white/90 shadow-[0_0_10px_rgba(255,255,255,0.6)] border border-gray-200" />
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto flex flex-col lg:flex-row gap-4 p-4 md:p-6">
        {/* Left Column */}
        <div className="lg:w-1/3 space-y-4">
          {/* Controls */}
          <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4">
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
              <div className="flex items-center gap-2">
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
            <div className="flex items-center gap-2">
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
