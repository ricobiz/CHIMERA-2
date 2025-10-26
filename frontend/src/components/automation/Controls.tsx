import React from 'react';
import { Play, Square, Pause, PlayCircle } from 'lucide-react';
import { Button } from '../ui/button';
import { Switch } from '../ui/switch';

interface ControlsProps {
  goal: string;
  onGoalChange: (goal: string) => void;
  onStart: () => void;
  onAbort: () => void;
  onPauseResume: () => void;
  sessionActive: boolean;
  blockInput: boolean;
  onBlockInputToggle: (enabled: boolean) => void;
  status: string;
  isPaused: boolean;
}

const Controls: React.FC<ControlsProps> = ({
  goal,
  onGoalChange,
  onStart,
  onAbort,
  onPauseResume,
  sessionActive,
  blockInput,
  onBlockInputToggle,
  status,
  isPaused
}) => {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
      <div className="flex flex-col lg:flex-row gap-4">
        {/* Goal Input */}
        <div className="flex-1">
          <label className="block text-xs font-medium text-gray-400 mb-2">
            Automation Goal
          </label>
          <textarea
            value={goal}
            onChange={(e) => onGoalChange(e.target.value)}
            placeholder="Describe what you want the agent to do (e.g., 'Register a new Gmail account')..."
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-300 text-sm placeholder-gray-600 focus:border-purple-500 focus:outline-none resize-none"
            rows={2}
            disabled={sessionActive}
          />
        </div>

        {/* Control Buttons */}
        <div className="flex flex-col justify-between gap-2 lg:w-auto">
          <div className="flex gap-2">
            {!sessionActive ? (
              <Button
                onClick={onStart}
                disabled={!goal.trim() || sessionActive}
                className="bg-green-600 hover:bg-green-500 text-white flex items-center gap-2"
              >
                <Play className="w-4 h-4" />
                START
              </Button>
            ) : (
              <>
                <Button
                  onClick={onPauseResume}
                  className="bg-yellow-600 hover:bg-yellow-500 text-white flex items-center gap-2"
                >
                  {isPaused ? (
                    <>
                      <PlayCircle className="w-4 h-4" />
                      RESUME
                    </>
                  ) : (
                    <>
                      <Pause className="w-4 h-4" />
                      PAUSE
                    </>
                  )}
                </Button>
                <Button
                  onClick={onAbort}
                  className="bg-red-600 hover:bg-red-500 text-white flex items-center gap-2"
                >
                  <Square className="w-4 h-4" />
                  ABORT
                </Button>
              </>
            )}
          </div>

          {/* Block Input Toggle */}
          <div className="flex items-center gap-3 px-3 py-2 bg-gray-800 border border-gray-700 rounded">
            <div className="flex-1">
              <p className="text-xs font-medium text-gray-300">Block User Input</p>
              <p className="text-[10px] text-gray-500">Agent has full control</p>
            </div>
            <Switch
              checked={blockInput}
              onCheckedChange={onBlockInputToggle}
              disabled={sessionActive}
              className="data-[state=checked]:bg-red-600"
            />
          </div>
        </div>
      </div>

      {/* Status Indicator */}
      {sessionActive && (
        <div className="mt-3 pt-3 border-t border-gray-800">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${
              status === 'executing' ? 'bg-blue-500 animate-pulse' :
              status === 'completed' ? 'bg-green-500' :
              status === 'failed' ? 'bg-red-500' :
              status === 'paused' ? 'bg-yellow-500' :
              'bg-gray-500'
            }`}></div>
            <span className="text-xs text-gray-400">
              Status: <span className="text-gray-300 font-medium capitalize">{status}</span>
              {isPaused && <span className="text-yellow-400 ml-1">(Paused)</span>}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default Controls;