import React from 'react';
import { CheckCircle, Circle, Clock, AlertCircle } from 'lucide-react';

const TaskProgress = ({ tasks = [], currentTaskIndex = 0 }) => {
  const totalTasks = tasks.length;
  const completedTasks = tasks.filter(t => t.status === 'completed').length;
  const progress = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'validating':
        return <Clock className="w-4 h-4 text-yellow-500 animate-pulse" />;
      case 'in-progress':
        return <Clock className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Circle className="w-4 h-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500/20 border-green-500';
      case 'validating':
        return 'bg-yellow-500/20 border-yellow-500';
      case 'in-progress':
        return 'bg-blue-500/20 border-blue-500';
      case 'error':
        return 'bg-red-500/20 border-red-500';
      default:
        return 'bg-gray-800 border-gray-700';
    }
  };

  if (tasks.length === 0) return null;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
      {/* Header with overall progress */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-medium text-gray-300">Development Plan</h3>
          <span className="text-xs text-gray-500">
            {completedTasks}/{totalTasks} completed
          </span>
        </div>
        
        {/* Progress bar */}
        <div className="relative h-2 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="absolute top-0 left-0 h-full bg-gradient-to-r from-blue-500 to-green-500 transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
          
          {/* Current position indicator */}
          <div
            className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full border-2 border-blue-500 shadow-lg transition-all duration-500"
            style={{ left: `${progress}%`, marginLeft: '-6px' }}
          />
        </div>
      </div>

      {/* Task list */}
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {tasks.map((task, index) => (
          <div
            key={index}
            className={`p-3 rounded-lg border transition-all duration-300 ${getStatusColor(task.status)} ${
              index === currentTaskIndex ? 'ring-2 ring-blue-500' : ''
            }`}
          >
            <div className="flex items-start gap-2">
              <div className="mt-0.5">
                {getStatusIcon(task.status)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-300 font-medium">{task.name}</p>
                {task.description && (
                  <p className="text-xs text-gray-500 mt-1">{task.description}</p>
                )}
                {task.status === 'validating' && (
                  <p className="text-xs text-yellow-400 mt-1 italic">Validating...</p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TaskProgress;
