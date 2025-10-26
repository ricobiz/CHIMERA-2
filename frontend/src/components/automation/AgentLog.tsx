import React, { useRef, useEffect } from 'react';
import { AgentLogEntry } from '../../agent/types.ts';
import { CheckCircle2, XCircle, Clock, RotateCcw } from 'lucide-react';

interface AgentLogProps {
  steps: AgentLogEntry[];
  goal: string;
  currentSubtask?: string;
}

const AgentLog: React.FC<AgentLogProps> = ({ steps, goal, currentSubtask }) => {
  const logEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new entries added
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [steps]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ok':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'fail':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'retrying':
        return <RotateCcw className="w-4 h-4 text-yellow-500 animate-spin" />;
      case 'pending':
      default:
        return <Clock className="w-4 h-4 text-blue-500 animate-pulse" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ok':
        return 'bg-green-900/30 border-green-700/50';
      case 'fail':
        return 'bg-red-900/30 border-red-700/50';
      case 'retrying':
        return 'bg-yellow-900/30 border-yellow-700/50';
      case 'pending':
      default:
        return 'bg-blue-900/30 border-blue-700/50';
    }
  };

  return (
    <div className="flex flex-col bg-gray-900 border border-gray-800 rounded-lg overflow-hidden" style={{ height: '100%', minHeight: '350px' }}>
      {/* Log Header */}
      <div className="px-4 py-3 bg-gray-800 border-b border-gray-700 flex-shrink-0">
        <h3 className="text-sm font-semibold text-gray-300 mb-1">Agent Execution Log</h3>
        {goal && (
          <div className="mt-2">
            <p className="text-xs text-gray-500 mb-1">Goal:</p>
            <p className="text-sm text-gray-300 font-medium">{goal}</p>
          </div>
        )}
        {currentSubtask && (
          <div className="mt-2">
            <p className="text-xs text-gray-500 mb-1">Current Subtask:</p>
            <p className="text-sm text-blue-400">{currentSubtask}</p>
          </div>
        )}
      </div>

      {/* Log Entries */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {steps.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-600">
            <Clock className="w-12 h-12 mb-3 text-gray-700" />
            <p className="text-sm">Waiting to start...</p>
          </div>
        ) : (
          steps.map((entry) => (
            <div
              key={entry.id}
              className={`border rounded-lg p-3 transition-all ${getStatusColor(entry.status)}`}
            >
              <div className="flex items-start gap-3">
                <div className="mt-0.5">{getStatusIcon(entry.status)}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-mono text-gray-500">{entry.timestamp}</span>
                    <span className="text-xs font-semibold text-gray-400 uppercase">
                      {entry.actionType}
                    </span>
                    {entry.retryAttempt && (
                      <span className="text-xs px-1.5 py-0.5 bg-yellow-900/50 text-yellow-400 rounded">
                        Retry #{entry.retryAttempt}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-300">{entry.details}</p>
                  {entry.error && (
                    <p className="text-xs text-red-400 mt-1 italic">Error: {entry.error}</p>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={logEndRef} />
      </div>

      {/* Log Stats */}
      <div className="px-4 py-2 bg-gray-800 border-t border-gray-700">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>{steps.length} entries</span>
          <span>
            {steps.filter(s => s.status === 'ok').length} completed • 
            {steps.filter(s => s.status === 'fail').length} failed
          </span>
        </div>
      </div>
    </div>
  );
};

export default AgentLog;