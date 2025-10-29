import React, { useState, useEffect, useRef } from 'react';
import { X, Pause, Play, Square, RotateCcw } from 'lucide-react';

const BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export const AutomationModal = ({ 
  isOpen, 
  onClose,
  initialTask 
}) => {
  const [logs, setLogs] = useState([]);
  const [status, setStatus] = useState('IDLE');
  const [sessionId, setSessionId] = useState(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [taskInput, setTaskInput] = useState(initialTask || '');
  
  // Automation Chat state
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  
  // Polling logs
  useEffect(() => {
    if (!isOpen) return;
    
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${BASE_URL}/api/hook/log`);
        const data = await res.json();
        setLogs(data.logs || []);
        setStatus(data.status || 'IDLE');
        setSessionId(data.session_id);
      } catch (e) {
        console.error('Failed to fetch logs:', e);
      }
    }, 1000);
    
    return () => clearInterval(interval);
  }, [isOpen]);
  
  // Polling automation chat history
  useEffect(() => {
    if (!isOpen || !isExecuting) return;
    
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${BASE_URL}/api/hook/automation-chat/history`);
        const data = await res.json();
        setChatMessages(data.history || []);
      } catch (e) {
        console.error('Failed to fetch chat history:', e);
      }
    }, 2000);
    
    return () => clearInterval(interval);
  }, [isOpen, isExecuting]);
  
  const startTask = async () => {
    if (!taskInput.trim()) return;
    
    setIsExecuting(true);
    
    try {
      const res = await fetch(`${BASE_URL}/api/hook/exec`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: taskInput,
          timestamp: Date.now(),
          nocache: true
        })
      });
      
      const data = await res.json();
      
      if (data.status === 'NEEDS_USER_DATA') {
        // TODO: Show data input dialog
        alert(`Task requires data: ${data.required_fields.join(', ')}`);
        setIsExecuting(false);
      }
    } catch (e) {
      console.error('Failed to start task:', e);
      alert('Failed to start task: ' + e.message);
      setIsExecuting(false);
    }
  };
  
  const sendChatMessage = async () => {
    if (!chatInput.trim()) return;
    
    const userMsg = { role: 'user', content: chatInput };
    setChatMessages(prev => [...prev, userMsg]);
    
    try {
      const res = await fetch(`${BASE_URL}/api/hook/automation-chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: chatInput
        })
      });
      
      const data = await res.json();
      const assistantMsg = { role: 'assistant', content: data.reply };
      setChatMessages(prev => [...prev, assistantMsg]);
      setChatInput('');
      
      // Update status if action was taken
      if (data.action) {
        setStatus(data.status);
      }
    } catch (e) {
      console.error('Failed to send message:', e);
    }
  };
  
  const handlePause = async () => {
    await sendChatMessage();
    setChatInput('Pause');
    await sendChatMessage();
  };
  
  const handleResume = async () => {
    setChatInput('Resume');
    await sendChatMessage();
  };
  
  const handleStop = async () => {
    setChatInput('Stop');
    await sendChatMessage();
    setIsExecuting(false);
  };
  
  const handleReset = async () => {
    setLogs([]);
    setStatus('IDLE');
    setSessionId(null);
    setIsExecuting(false);
    setChatMessages([]);
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="w-full max-w-7xl h-[90vh] bg-gray-900 border border-gray-700 rounded-lg shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-purple-500 animate-pulse"></div>
            <h2 className="text-lg font-semibold text-white">Automation Mode</h2>
            <span className={`px-2 py-1 text-xs rounded ${
              status === 'ACTIVE' ? 'bg-green-900/30 text-green-400 border border-green-600/50' :
              status === 'PAUSED' ? 'bg-yellow-900/30 text-yellow-400 border border-yellow-600/50' :
              status === 'ERROR' ? 'bg-red-900/30 text-red-400 border border-red-600/50' :
              'bg-gray-800 text-gray-400 border border-gray-700'
            }`}>
              {status}
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-gray-800/50 hover:bg-gray-700/50 border border-gray-700 hover:border-gray-600 transition-all"
          >
            <X className="w-4 h-4 text-gray-300" />
          </button>
        </div>
        
        {/* Main Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left: Browser Viewport + Logs */}
          <div className="flex-1 flex flex-col border-r border-gray-700">
            {/* Browser Viewport (Placeholder) */}
            <div className="flex-1 bg-gray-950 border-b border-gray-700 p-4 overflow-auto">
              <div className="w-full h-full border border-gray-700 rounded-lg bg-gray-900/50 flex items-center justify-center text-gray-500">
                Browser Viewport (Coming Soon)
                {sessionId && <div className="text-xs mt-2">Session: {sessionId.slice(0, 8)}</div>}
              </div>
            </div>
            
            {/* Logs */}
            <div className="h-48 bg-gray-900 p-3 overflow-auto">
              <div className="text-xs font-mono space-y-1">
                {logs.map((log, i) => (
                  <div key={i} className="text-gray-400">
                    <span className="text-gray-600">[{log.step}]</span> {log.action}
                  </div>
                ))}
              </div>
            </div>
          </div>
          
          {/* Right: Chat + Controls */}
          <div className="w-96 flex flex-col bg-gray-900">
            {/* Controls */}
            <div className="p-4 border-b border-gray-700 space-y-3">
              {!isExecuting ? (
                <>
                  <input
                    type="text"
                    value={taskInput}
                    onChange={(e) => setTaskInput(e.target.value)}
                    placeholder="Enter task..."
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-purple-600"
                    onKeyDown={(e) => e.key === 'Enter' && startTask()}
                  />
                  <button
                    onClick={startTask}
                    disabled={!taskInput.trim()}
                    className="w-full px-4 py-2 bg-purple-600/20 hover:bg-purple-600/30 border border-purple-600/50 text-purple-300 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                  >
                    Start Task
                  </button>
                </>
              ) : (
                <div className="flex gap-2">
                  {status === 'PAUSED' ? (
                    <button onClick={handleResume} className="flex-1 px-3 py-2 bg-green-600/20 hover:bg-green-600/30 border border-green-600/50 text-green-400 rounded-lg text-sm flex items-center justify-center gap-2">
                      <Play className="w-4 h-4" /> Resume
                    </button>
                  ) : (
                    <button onClick={handlePause} className="flex-1 px-3 py-2 bg-yellow-600/20 hover:bg-yellow-600/30 border border-yellow-600/50 text-yellow-400 rounded-lg text-sm flex items-center justify-center gap-2">
                      <Pause className="w-4 h-4" /> Pause
                    </button>
                  )}
                  <button onClick={handleStop} className="flex-1 px-3 py-2 bg-red-600/20 hover:bg-red-600/30 border border-red-600/50 text-red-400 rounded-lg text-sm flex items-center justify-center gap-2">
                    <Square className="w-4 h-4" /> Stop
                  </button>
                  <button onClick={handleReset} className="px-3 py-2 bg-gray-600/20 hover:bg-gray-600/30 border border-gray-600/50 text-gray-400 rounded-lg text-sm">
                    <RotateCcw className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
            
            {/* Automation Chat */}
            <div className="flex-1 flex flex-col overflow-hidden">
              <div className="px-4 py-2 border-b border-gray-700 text-sm font-medium text-gray-400">
                Chat with Automation Brain
              </div>
              
              {/* Messages */}
              <div className="flex-1 overflow-auto p-4 space-y-3">
                {chatMessages.map((msg, i) => (
                  <div key={i} className={`${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
                    <div className={`inline-block px-3 py-2 rounded-lg text-sm ${
                      msg.role === 'user' 
                        ? 'bg-purple-600/20 text-purple-200 border border-purple-600/50'
                        : 'bg-gray-800 text-gray-200 border border-gray-700'
                    }`}>
                      {msg.content}
                    </div>
                  </div>
                ))}
              </div>
              
              {/* Input */}
              {isExecuting && (
                <div className="p-4 border-t border-gray-700">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      placeholder="Type a message..."
                      className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-purple-600"
                      onKeyDown={(e) => e.key === 'Enter' && sendChatMessage()}
                    />
                    <button
                      onClick={sendChatMessage}
                      disabled={!chatInput.trim()}
                      className="px-4 py-2 bg-purple-600/20 hover:bg-purple-600/30 border border-purple-600/50 text-purple-300 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                    >
                      Send
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
