import React, { useState, useEffect, useRef } from 'react';
import { Play, RefreshCw, FileText, Activity, AlertCircle, CheckCircle, Pause, Square, Link, Copy } from 'lucide-react';
import { sendTask, getLogs, refreshAgent, getCurrentTask, getAgentStatus, getResult, controlAgent, automationCreateSession, automationNavigate, automationScreenshot, automationClickCell, automationTypeAtCell, automationHoldDrag, automationScroll, brainNextStep } from '../services/agentApi';

const AIEntryPoint = ({ onClose }) => {
  // State
  const [taskText, setTaskText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [logs, setLogs] = useState([]);
  const [agentStatus, setAgentStatus] = useState('IDLE');
  const [currentTask, setCurrentTask] = useState('');
  const [profileHealth, setProfileHealth] = useState({ profile_id: null, is_warm: false, is_clean: null, last_check: null, proxy: null });
  const [showFullscreen, setShowFullscreen] = useState(false);
  const [showGrid, setShowGrid] = useState(true);

  const [result, setResult] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [goal, setGoal] = useState('Register a new Gmail and return login/password');
  const [logs, setLogs] = useState([]);
  const [agentStatus, setAgentStatus] = useState('IDLE');
  const [jobId, setJobId] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [observation, setObservation] = useState(null);
  const [askUser, setAskUser] = useState(null);
  const viewerRef = useRef(null);
  const [displaySrc, setDisplaySrc] = useState(null);
  const [pendingSrc, setPendingSrc] = useState(null);
  const lastUpdateRef = useRef(0);
  const pollRef = useRef(null);

  // Helper to convert cell (e.g., C7) to percentage within container
  const cellToPercent = (cell, grid) => {
    if (!cell || !grid) return { left: 50, top: 50 };
    const colLetter = cell[0].toUpperCase();
    const rowNum = parseInt(cell.slice(1), 10);
    const colIndex = colLetter.charCodeAt(0) - 'A'.charCodeAt(0);
    const rowIndex = rowNum - 1;
    const left = ((colIndex + 0.5) / (grid.cols || 8)) * 100;
    const top = ((rowIndex + 0.5) / (grid.rows || 12)) * 100;
    return { left, top };
  };

  // Preload pending screenshot and swap to displaySrc on load for smoothness
  useEffect(() => {
    if (!pendingSrc) return;
    const img = new Image();
    img.onload = () => {
      setDisplaySrc(pendingSrc);
    };
    img.src = `data:image/png;base64,${pendingSrc}`;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingSrc]);

  const [lastAutomation, setLastAutomation] = useState(null);
  const [runMode, setRunMode] = useState('PAUSED');
  const [accessEnabled, setAccessEnabled] = useState(false);
  const [sessionLink, setSessionLink] = useState('');
  
  const logsEndRef = useRef(null);
  const pollIntervalRef = useRef(null);

  // Auto-scroll to bottom when new logs arrive
  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [logs]);

  // Poll for logs every 1500ms when auto-refresh is on
  useEffect(() => {
    if (autoRefresh) {
      pollIntervalRef.current = setInterval(async () => {
        try {
          const data = await getLogs(false);
          setLogs(data.logs || []);
          setAgentStatus(data.status || 'IDLE');
        } catch (error) {
          console.error('Error polling logs:', error);
        }
      }, 1500);
    } else {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [autoRefresh]);

  // Load current task on mount
  useEffect(() => {
    loadCurrentTask();
    loadResult();
    loadStatus();
    generateSessionLink();
  }, []);

  const generateSessionLink = () => {
    const sessionId = `sess-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const link = `${window.location.origin}/ai-entry?session=${sessionId}`;
    setSessionLink(link);
  };

  const toggleAccess = () => {
    setAccessEnabled(!accessEnabled);
    if (!accessEnabled) {
      generateSessionLink(); // Generate new link when enabling access
    }
  };

  const copyLink = () => {
    navigator.clipboard.writeText(sessionLink);
    alert('Ссылка скопирована в буфер обмена!');
  };

  const loadStatus = async () => {
    try {
      const data = await getAgentStatus();
      setAgentStatus(data.status || 'IDLE');
      setRunMode(data.run_mode || 'PAUSED');
    } catch (error) {
      console.error('Error loading status:', error);
    }
  };

  const loadCurrentTask = async () => {
    try {
      const data = await getCurrentTask();
      setCurrentTask(data.text || '');
    } catch (error) {
      console.error('Error loading current task:', error);
    }
  };

  const loadResult = async () => {
    try {
      const data = await getResult();
      if (data.result) {
        setResult(data.result);
      }
    } catch (error) {
      console.error('Error loading result:', error);
    }
  };

  const handleRunTask = async () => {
    if (!taskText.trim()) {
      alert('Please enter a task description');
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await sendTask(taskText);
      setJobId(response.job_id);
      setCurrentTask(taskText);
      setAgentStatus('ACTIVE');
      
      // Clear previous logs and wait for new ones
      setLogs([]);
      setAutoRefresh(true);
      
      alert(`Task accepted! Job ID: ${response.job_id}`);
    } catch (error) {
      alert(`Error: ${error.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleForceExecute = async () => {
    try {
      await sendTask('run');
      alert('Force execute triggered');
    } catch (error) {
      alert(`Error: ${error.message}`);
    }
  };

  const handleForceRefresh = async () => {
    try {
      const response = await refreshAgent('main');
      alert(`Agent refreshed: ${response.status}`);
    } catch (error) {
      alert(`Error: ${error.message}`);
    }
  };

  const handleReadLogs = async () => {
    try {
      const data = await getLogs(true);
      setLogs(data.logs || []);
      setAgentStatus(data.status || 'IDLE');
            <div className="relative border border-gray-800 rounded bg-black/60 overflow-hidden">
              <div className="flex items-center justify-between p-2 border-b border-gray-800 bg-black/40">
                <div className="text-xs text-gray-400">Live Agent View</div>
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] px-2 py-0.5 rounded ${agentStatus==='ACTIVE'?'bg-green-900/40 text-green-300':agentStatus==='PAUSED'?'bg-yellow-900/40 text-yellow-300':agentStatus==='WAITING_USER'?'bg-blue-900/40 text-blue-300':agentStatus==='ERROR'?'bg-red-900/40 text-red-300':'bg-gray-900/40 text-gray-300'}`}>{agentStatus}</span>
                  <button onClick={() => setShowGrid(!showGrid)} className="px-2 py-1 text-xs bg-gray-800/60 hover:bg-gray-700/60 border border-gray-700 rounded text-gray-300">{showGrid ? 'Hide Grid' : 'Show Grid'}</button>
                  <button onClick={() => setShowFullscreen(true)} className="px-2 py-1 text-xs bg-gray-800/60 hover:bg-gray-700/60 border border-gray-700 rounded text-gray-300">Fullscreen</button>
                </div>
              </div>
              <div ref={viewerRef} className="relative w-full h-72 md:h-[420px] flex items-center justify-center bg-black">
                {displaySrc ? (
                  <img src={`data:image/png;base64,${displaySrc}`} alt="screenshot" className="max-w-full max-h-full object-contain" />
                ) : (
                  <div className="text-xs text-gray-600">No screenshot</div>
                )}
                {/* Grid overlay */}
                {showGrid && lastAutomation?.grid && (
                  <div className="absolute inset-0 pointer-events-none">
                    <div className="w-full h-full" style={{ backgroundImage: `linear-gradient(rgba(200,200,200,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(200,200,200,0.08) 1px, transparent 1px)`, backgroundSize: `${(100/lastAutomation.grid.cols)}% ${(100/lastAutomation.grid.rows)}%`}} />
                  </div>
                )}
                {/* Ghost cursor based on last step */}
                {(() => {
                  const last = (logs || []).slice().reverse().find(l => l.action && l.action.startsWith('Step'));
                  const step = (logs || []).slice().reverse().find(l => l.action && (l.action.includes('CLICK_CELL') || l.action.includes('TYPE_AT_CELL') || l.action.includes('HOLD_DRAG')));
                  const cell = step?.action?.match(/[A-H][0-9]{1,2}/)?.[0];
                  const grid = lastAutomation?.grid || { rows: 12, cols: 8 };
                  const pos = cellToPercent(cell, grid);
                  return cell ? (
                    <div className="absolute" style={{ left: `${pos.left}%`, top: `${pos.top}%`, transform: 'translate(-50%, -50%)' }}>
                      <div className="w-4 h-4 rounded-full bg-white/90 shadow-[0_0_10px_rgba(255,255,255,0.6)] border border-gray-200" />
                    </div>
                  ) : null;
                })()}
              </div>
            </div>

      alert(`Loaded ${data.logs?.length || 0} log entries`);
    } catch (error) {
      alert(`Error: ${error.message}`);
    }
  };

  const handleControlMode = async (mode) => {
    try {
      const response = await controlAgent(mode);
      setRunMode(response.run_mode);
      setAgentStatus(response.agent_status);
      
      // Reload result if completed
      if (mode === 'STOP') {
        loadResult();
      }
    } catch (error) {
      alert(`Error: ${error.message}`);
    }
  };

  const getStatusColor = () => {
    switch (agentStatus) {
      case 'ACTIVE': return 'text-green-400';
      case 'ERROR': return 'text-red-400';
      case 'IDLE': return 'text-gray-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusIcon = () => {
    switch (agentStatus) {
      case 'ACTIVE': return <Activity className="w-5 h-5 animate-pulse" />;
      case 'ERROR': return <AlertCircle className="w-5 h-5" />;
      default: return <Activity className="w-5 h-5" />;
    }
  };

  return (
    <div className="flex flex-col bg-[#0f0f10] text-gray-100 overflow-x-hidden" style={{ height: '100dvh' }}>
      {/* Header */}
      <div className="px-4 md:px-6 py-4 border-b border-gray-800 flex-shrink-0">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            {onClose && (
              <button
                onClick={onClose}
                className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors flex items-center gap-2 text-sm"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back
              </button>
            )}
            <div>
              <h1 className="text-xl md:text-2xl font-bold text-white">AI Entry Point</h1>
              <p className="text-xs md:text-sm text-gray-400">Universal gateway between orchestrator AI and execution agent</p>
            </div>
          </div>
          {/* Live Preview + Vision */}
          <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-gray-400 font-medium">Live Preview</span>
              <button
                onClick={async () => {
            <div className="flex items-center gap-2">
              <button onClick={() => setShowGrid(!showGrid)} className="px-2 py-1 text-xs bg-gray-800/60 hover:bg-gray-700/60 border border-gray-700 rounded text-gray-300">{showGrid ? 'Hide Grid' : 'Show Grid'}</button>
              <button onClick={() => setShowFullscreen(true)} className="px-2 py-1 text-xs bg-gray-800/60 hover:bg-gray-700/60 border border-gray-700 rounded text-gray-300">Fullscreen</button>
            </div>

                  try {
                    const sessionId = 'auto-'+(Date.now());
                    await automationCreateSession(sessionId, true);
                    await automationNavigate(sessionId, 'https://accounts.google.com/signup');
                    const shot = await automationScreenshot(sessionId);
                    setLogs(prev => [...prev, { ts: Date.now(), step: prev.length+1, action: 'Session initialized & navigated', status: 'ok' }]);
                    setLastAutomation({ sessionId, ...shot });
                  } catch (e) {
                    alert('Automation init failed: '+ e.message);
                  }
                }}
                className="px-3 py-1.5 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-600/40 text-blue-400 rounded text-xs"
              >Start Session</button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="border border-gray-800 rounded p-2 bg-black/50">
                {lastAutomation?.screenshot_base64 ? (
                  <img
                    src={`data:image/png;base64,${lastAutomation.screenshot_base64}`}
                    alt="screenshot"
                {showGrid && (
                  <div className="absolute inset-0 pointer-events-none">
                    {/* simple CSS grid overlay */}
                    <div className="w-full h-full" style={{ backgroundImage: `linear-gradient(rgba(200,200,200,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(200,200,200,0.08) 1px, transparent 1px)`, backgroundSize: `${(lastAutomation?.grid?.cols ? 100/lastAutomation.grid.cols : 12.5)}% ${(lastAutomation?.grid?.rows ? 100/lastAutomation.grid.rows : 8.333)}%`}} />
                  </div>
                )}

                    className="w-full object-contain rounded"
                  />
                ) : (
                  <div className="text-xs text-gray-600 text-center py-8">No screenshot</div>
                )}
              </div>
              <div className="border border-gray-800 rounded p-2">
                <div className="text-xs text-gray-500 mb-2">Vision Elements</div>
                <div className="max-h-64 overflow-y-auto">
                  {(lastAutomation?.vision || []).map((v, idx) => (
                    <div key={idx} className="text-xs text-gray-300 flex gap-2 py-1 border-b border-gray-800/50">
                      <span className="text-gray-500 w-10">{v.cell}</span>
                      <span className="flex-1 truncate">{v.label}</span>
                      <span className="text-gray-400 w-20">{v.type}</span>
                      <span className="text-gray-500 w-12">{(v.confidence*100|0)}%</span>
                    </div>
                  ))}
                  {(!lastAutomation?.vision || lastAutomation.vision.length===0) && (
                    <div className="text-xs text-gray-600 text-center py-6">No vision data</div>
                  )}
                </div>
            {showFullscreen && (
              <div className="fixed inset-0 bg-black/90 z-[100] p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm text-gray-400">Fullscreen Viewer</div>
                  <button onClick={() => setShowFullscreen(false)} className="px-3 py-1 text-xs bg-gray-800/60 hover:bg-gray-700/60 border border-gray-700 rounded text-gray-300">Close</button>
                </div>
                <div className="w-full h-[calc(100%-40px)] border border-gray-800 rounded bg-black flex items-center justify-center">
                  {lastAutomation?.screenshot_base64 ? (
                    <img src={`data:image/png;base64,${lastAutomation.screenshot_base64}`} alt="screenshot-full" className="max-w-full max-h-full object-contain" />
                  ) : (
                    <div className="text-xs text-gray-600">No screenshot</div>
                  )}
                </div>
              </div>
            )}

              </div>
            </div>
          </div>

        </div>
      </div>

      {/* Main Content - with scrolling */}
      <div className="flex-1 overflow-y-auto flex flex-col lg:flex-row gap-4 p-4 md:p-6">
        
        {/* Left Column: Task Input + Quick Actions */}
        <div className="lg:w-1/3 space-y-4">
          
          {/* External Access Link */}
          <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-gray-400 font-medium">🔗 External AI Access</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={accessEnabled}
                  onChange={toggleAccess}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
              </label>
            </div>
            
            {accessEnabled ? (
              <>
                <p className="text-xs text-gray-500 mb-3">
                  Поделитесь этой ссылкой с внешним AI для доступа к агенту:
          {/* Waiting User Modal */}
          {askUser && (
            <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
              <div className="bg-[#0f0f10] border border-gray-800 rounded-lg w-full max-w-md p-4">
                <div className="text-sm text-gray-300 mb-2">Agent needs your input</div>
                <div className="text-xs text-gray-400 mb-3">{askUser}</div>
                <div className="flex items-center gap-2">
                  <input id="user_input_field" className="flex-1 px-2 py-1 text-xs bg-gray-900 border border-gray-700 rounded text-gray-300" placeholder="Enter value (phone/code)" />
                  <button onClick={async() => {
                    const val = document.getElementById('user_input_field').value;
                    if (!jobId) return;
                    await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/hook/user_input`, { method: 'POST', headers: { 'Content-Type':'application/json' }, body: JSON.stringify({ job_id: jobId, field: 'code', value: val })});
                    setAskUser(null);
                  }} className="px-3 py-1.5 text-xs bg-blue-600/20 hover:bg-blue-600/30 border border-blue-600/50 text-blue-300 rounded">Submit</button>
                  <button onClick={() => setAskUser(null)} className="px-3 py-1.5 text-xs bg-gray-800/20 hover:bg-gray-800/30 border border-gray-700 text-gray-300 rounded">Cancel</button>
                </div>
              </div>
            </div>
          )}

                </p>
                <div className="bg-gray-800/50 border border-gray-700 rounded p-2 mb-2 flex items-center gap-2">
                  <input
                    type="text"
                    value={sessionLink}
                    readOnly
                    className="flex-1 bg-transparent text-xs text-gray-300 outline-none"
                  />
                  <button
                    onClick={copyLink}
                    className="px-2 py-1 bg-purple-600/20 hover:bg-purple-600/30 border border-purple-600/50 text-purple-400 rounded text-xs transition-colors"
                  >
          {/* Controls */}
          <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-sm text-gray-400 font-medium">Controls</span>
            </div>
            <div className="flex gap-2">
              <button onClick={() => handleControlMode('ACTIVE')} className="px-3 py-1.5 bg-green-600/20 hover:bg-green-600/30 border border-green-600/50 text-green-400 rounded text-xs">Resume</button>
              <button onClick={() => handleControlMode('PAUSED')} className="px-3 py-1.5 bg-yellow-600/20 hover:bg-yellow-600/30 border border-yellow-600/50 text-yellow-400 rounded text-xs">Pause</button>
              <button onClick={() => handleControlMode('STOP')} className="px-3 py-1.5 bg-red-600/20 hover:bg-red-600/30 border border-red-600/50 text-red-400 rounded text-xs">Stop</button>
            </div>
          </div>

                    Copy
                  </button>
                </div>
                <p className="text-xs text-green-400">
                  ✓ Доступ активирован для этой сессии
                </p>
              </>
            ) : (
              <p className="text-xs text-gray-500">
                Включите переключатель, чтобы сгенерировать ссылку для внешнего AI.
              </p>
            )}
          </div>
          
          {/* Agent Status */}
          {/* Step Timeline */}
          <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-gray-400 font-medium">Step Timeline</span>
            </div>
            <div className="max-h-64 overflow-y-auto space-y-1">
              {(logs || []).map((l, idx) => (
                <div key={idx} className="text-xs text-gray-300 flex items-center gap-2">
                  <span className="text-gray-500 w-16">Step {l.step}</span>
                  <span className="flex-1 truncate">{l.action}</span>
                  <span className={`w-12 text-right ${l.status==='ok'?'text-green-400':l.status==='error'?'text-red-400':'text-gray-400'}`}>{l.status}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Profile Health */}
          <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-gray-400 font-medium">Profile Health</span>
              <div className="flex gap-2">
                <button
                  onClick={async () => {
                    const profId = window.currentProfileId || prompt('Profile ID to re-check:');
                    if (!profId) return;
                    try {
                      const resp = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/profile/check`, {
                        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ profile_id: profId })
                      });
                      const data = await resp.json();
                      alert(`Re-check done. Clean=${data.is_clean}`);
                    } catch (e) {
                      alert('Re-check failed: '+ e.message);
                    }
                  }}
                  className="px-3 py-1.5 bg-purple-600/20 hover:bg-purple-600/30 border border-purple-600/50 text-purple-300 rounded text-xs"
                >Re-check profile now</button>
              </div>
            </div>
            <div className="text-xs text-gray-400 space-y-1">
              <div>profile_id: <span className="text-gray-200">{window.currentProfileId || '—'}</span></div>
              <div>proxy/region: <span className="text-gray-200">{lastProfileHealth?.proxy || '—'}</span></div>
              <div>warm: <span className="text-gray-200">{lastProfileHealth?.is_warm ? 'yes' : 'no'}</span></div>
              <div>clean: <span className="text-gray-200">{lastProfileHealth?.is_clean ? '✅' : '❌'}</span></div>
              <div>last check: <span className="text-gray-200">{lastProfileHealth?.last_check || '—'}</span></div>
            </div>
          </div>

          <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400 font-medium">Agent Status</span>
              {getStatusIcon()}
            </div>
            <div className={`text-2xl font-bold ${getStatusColor()}`}>
              {agentStatus}
            </div>
            <div className="mt-1 text-sm text-gray-500">
              Mode: <span className={runMode === 'ACTIVE' ? 'text-green-400' : 'text-gray-400'}>{runMode}</span>
            </div>
            
            {/* Control Buttons */}
            <div className="mt-3 flex gap-2">
              <button
                onClick={() => handleControlMode('ACTIVE')}
                disabled={runMode === 'ACTIVE'}
                className="flex-1 px-3 py-1.5 bg-green-600/20 hover:bg-green-600/30 border border-green-600/50 text-green-400 rounded text-xs font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1"
              >
                <Play className="w-3 h-3" />
                Activate
              </button>
              <button
                onClick={() => handleControlMode('PAUSED')}
                disabled={runMode === 'PAUSED'}
                className="flex-1 px-3 py-1.5 bg-yellow-600/20 hover:bg-yellow-600/30 border border-yellow-600/50 text-yellow-400 rounded text-xs font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1"
              >
                <Pause className="w-3 h-3" />
                Pause
              </button>
              <button
                onClick={() => handleControlMode('STOP')}
                className="flex-1 px-3 py-1.5 bg-red-600/20 hover:bg-red-600/30 border border-red-600/50 text-red-400 rounded text-xs font-medium transition-colors flex items-center justify-center gap-1"
              >
                <Square className="w-3 h-3" />
                Stop
              </button>
            </div>
            
            <div className="mt-3 flex items-center gap-2">
              <label className="text-xs text-gray-500 flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="rounded"
                />
                Auto-refresh logs
              </label>
            </div>
          </div>

          {/* Current Task */}
          <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <FileText className="w-4 h-4 text-blue-400" />
              <span className="text-sm text-gray-400 font-medium">CURRENT TASK</span>
            </div>
            <div className="text-sm text-gray-300 break-words">
              {currentTask || <span className="text-gray-600 italic">No active task</span>}
            </div>
            {jobId && (
              <div className="mt-2 text-xs text-gray-500 font-mono">
                Job ID: {jobId}
              </div>
            )}
          </div>

          {/* Task Input */}
          <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4">
            <label className="block text-sm text-gray-400 font-medium mb-3">Task Input</label>
            <textarea
              value={taskText}
              onChange={(e) => setTaskText(e.target.value)}
              placeholder="Enter task in natural language...

Example: Register new Gmail account, bypass CAPTCHA, return login/password and confirmation screenshot"
              className="w-full h-32 bg-gray-950 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-blue-500 resize-none"
            />
            <button
              onClick={handleRunTask}
              disabled={isSubmitting || !taskText.trim()}
              className="mt-3 w-full px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
            >
              <Play className="w-4 h-4" />
              {isSubmitting ? 'Sending...' : 'Run Task'}
            </button>
          </div>

          {/* Quick Actions */}
          <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4">
            <label className="block text-sm text-gray-400 font-medium mb-3">Quick Actions</label>
            <div className="space-y-2">
              <button
                onClick={handleForceExecute}
                className="w-full px-3 py-2 bg-red-600/20 hover:bg-red-600/30 border border-red-600/50 text-red-400 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
              >
                💥 Force Execute
              </button>
              <button
                onClick={handleForceRefresh}
                className="w-full px-3 py-2 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-600/50 text-blue-400 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
              >
                🔁 Force Refresh
              </button>
              <button
                onClick={handleReadLogs}
                className="w-full px-3 py-2 bg-green-600/20 hover:bg-green-600/30 border border-green-600/50 text-green-400 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
              >
                📊 Read Logs
              </button>
            </div>
          </div>

          {/* Result */}
          <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <label className="text-sm text-gray-400 font-medium">RESULT</label>
              {result?.completed && <CheckCircle className="w-4 h-4 text-green-400" />}
            </div>
            {result && result.completed ? (
              <div className="space-y-3">
                {result.credentials && (
                  <div className="bg-gray-950 rounded p-3 border border-gray-700">
                    <div className="text-xs text-gray-500 mb-2">Credentials:</div>
                    <div className="space-y-1 text-sm font-mono">
                      <div className="flex items-center gap-2">
                        <span className="text-gray-400">Login:</span>
                        <span className="text-green-400">{result.credentials.login}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-gray-400">Pass:</span>
                        <span className="text-green-400">{result.credentials.password}</span>
                      </div>
                    </div>
                  </div>
                )}
                {result.screenshot && (
                  <div className="bg-gray-950 rounded p-3 border border-gray-700">
                    <div className="text-xs text-gray-500 mb-2">Screenshot:</div>
                    <div className="text-sm text-blue-400 font-mono break-all">
                      {result.screenshot}
                    </div>
                  </div>
                )}
                <button
                  onClick={loadResult}

                  className="w-full px-3 py-2 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-600/50 text-blue-400 rounded text-sm font-medium transition-colors"
                >
                  Refresh Result
                </button>
              </div>
            ) : (
              <div className="text-sm text-gray-600 italic text-center py-4">
                {result === null 
                  ? 'Final artifacts will appear here...'
                  : 'Task in progress...'
                }
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Execution Logs */}
        <div className="lg:w-2/3">
          <div className="bg-black border border-gray-800 rounded-lg h-full flex flex-col">
            {/* Log Header */}
            <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-green-400" />
                <span className="text-sm text-green-400 font-mono">EXECUTION LOG</span>
              </div>
              <span className="text-xs text-gray-600">
                {logs.length} entries
              </span>
            </div>

            {/* Log Content */}
            <div className="flex-1 overflow-y-auto p-4 font-mono text-sm">
              {logs.length === 0 ? (
                <div className="text-gray-600 text-center py-12">
                  No logs yet. Run a task to see execution steps...
                </div>
              ) : (
                <div className="space-y-1">
                  {logs.map((log, idx) => (
                    <div
                      key={idx}
                      className={`flex gap-3 ${
                        log.status === 'error' ? 'text-red-400' :
                        log.status === 'warning' ? 'text-yellow-400' :
                        log.status === 'ok' ? 'text-green-400' :
                        'text-gray-400'
                      }`}
                    >
                      <span className="text-gray-600">[{new Date(log.ts).toLocaleTimeString()}]</span>
                      <span className="text-gray-500">Step {log.step}:</span>
                      <span>{log.action}</span>
                      {log.error && (
                        <span className="text-red-500">→ ERROR: {log.error}</span>
                      )}
                    </div>
                  ))}
                  <div ref={logsEndRef} />
                </div>
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default AIEntryPoint;
