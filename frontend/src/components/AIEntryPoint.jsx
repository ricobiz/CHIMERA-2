import React, { useState, useEffect, useRef } from 'react';
import { Play, RefreshCw, FileText, Activity, AlertCircle } from 'lucide-react';
import { sendTask, getLogs, refreshAgent, getCurrentTask, getAgentStatus } from '../services/agentApi';

const AIEntryPoint = () => {
  // State
  const [taskText, setTaskText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [logs, setLogs] = useState([]);
  const [agentStatus, setAgentStatus] = useState('IDLE');
  const [currentTask, setCurrentTask] = useState('');
  const [result, setResult] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  
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
  }, []);

  const loadCurrentTask = async () => {
    try {
      const data = await getCurrentTask();
      setCurrentTask(data.text || '');
    } catch (error) {
      console.error('Error loading current task:', error);
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
      alert(`Loaded ${data.logs?.length || 0} log entries`);
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
    <div className="flex flex-col h-screen bg-[#0f0f10] text-gray-100">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-800 flex-shrink-0">
        <h1 className="text-2xl font-bold text-white mb-1">AI Entry Point</h1>
        <p className="text-sm text-gray-400">Universal gateway between orchestrator AI and execution agent</p>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden flex flex-col lg:flex-row gap-4 p-6">
        
        {/* Left Column: Task Input + Quick Actions */}
        <div className="lg:w-1/3 space-y-4">
          
          {/* Agent Status */}
          <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400 font-medium">Agent Status</span>
              {getStatusIcon()}
            </div>
            <div className={`text-2xl font-bold ${getStatusColor()}`}>
              {agentStatus}
            </div>
            <div className="mt-2 flex items-center gap-2">
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

          {/* Result (Reserved) */}
          <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4">
            <label className="block text-sm text-gray-400 font-medium mb-2">RESULT</label>
            <div className="text-sm text-gray-600 italic">
              {result ? (
                <pre className="text-green-400 whitespace-pre-wrap">{JSON.stringify(result, null, 2)}</pre>
              ) : (
                'Final artifacts will appear here...'
              )}
            </div>
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
