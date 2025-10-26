import React, { useState, useEffect } from 'react';
import BrowserViewport from './BrowserViewport.tsx';
import AgentLog from './AgentLog.tsx';
import Controls from './Controls.tsx';
import { AutomationSession, BrowserState, AgentLogEntry } from '../../agent/types.ts';
import { executionAgent } from '../../agent/executionAgent.ts';
import { toast } from '../../hooks/use-toast';

const AutomationPage: React.FC<{ onClose?: () => void }> = ({ onClose }) => {
  const [session, setSession] = useState<AutomationSession>({
    sessionId: `session-${Date.now()}`,
    goal: '',
    plan: null,
    browserState: {
      currentUrl: '',
      screenshot: '',
      highlightBoxes: [],
      pageTitle: '',
      timestamp: Date.now()
    },
    logEntries: [],
    status: 'idle',
    currentStepIndex: -1,
    blockInput: false,
    requiresUserInput: null,
    result: null
  });

  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    // Set up state callback for execution agent
    executionAgent.setStateCallback((updates) => {
      setSession(prev => {
        const newSession = { ...prev };

        // Handle log entries specially (append, don't replace)
        if (updates.logEntries && updates.logEntries.length > 0) {
          const newEntry = updates.logEntries[0];
          
          // Check if this is an update to existing entry (has partial data)
          if (newEntry.id && !newEntry.timestamp) {
            // Update last entry
            const lastIndex = newSession.logEntries.length - 1;
            if (lastIndex >= 0) {
              newSession.logEntries[lastIndex] = {
                ...newSession.logEntries[lastIndex],
                ...newEntry
              };
            }
          } else {
            // Add new entry
            newSession.logEntries = [...newSession.logEntries, newEntry];
          }
          
          delete updates.logEntries; // Don't merge this
        }

        // Merge other updates
        return { ...newSession, ...updates };
      });
    });
  }, []);

  const handleStart = async () => {
    if (!session.goal.trim()) {
      toast({
        title: 'Goal Required',
        description: 'Please enter an automation goal',
        variant: 'destructive'
      });
      return;
    }

    // Reset session
    const newSession: AutomationSession = {
      sessionId: `session-${Date.now()}`,
      goal: session.goal,
      plan: null,
      browserState: {
        currentUrl: '',
        screenshot: '',
        highlightBoxes: [],
        pageTitle: '',
        timestamp: Date.now()
      },
      logEntries: [],
      status: 'planning',
      currentStepIndex: -1,
      blockInput: session.blockInput,
      requiresUserInput: null,
      result: null,
      startTime: Date.now()
    };

    setSession(newSession);
    setIsPaused(false);

    toast({
      title: 'Automation Started',
      description: `Starting automation: "${session.goal.substring(0, 50)}..."`,
    });

    // Start execution
    try {
      await executionAgent.startAutomation(session.goal, newSession);
    } catch (error: any) {
      toast({
        title: 'Automation Error',
        description: error.message,
        variant: 'destructive'
      });
    }
  };

  const handleAbort = () => {
    executionAgent.abort();
    setSession(prev => ({
      ...prev,
      status: 'failed',
      endTime: Date.now()
    }));
    setIsPaused(false);

    toast({
      title: 'Automation Aborted',
      description: 'The automation has been stopped',
      variant: 'destructive'
    });
  };

  const handlePauseResume = () => {
    if (isPaused) {
      executionAgent.resume();
      setIsPaused(false);
      setSession(prev => ({ ...prev, status: 'executing' }));
      toast({
        title: 'Automation Resumed',
        description: 'Agent is continuing execution',
      });
    } else {
      executionAgent.pause();
      setIsPaused(true);
      setSession(prev => ({ ...prev, status: 'paused' }));
      toast({
        title: 'Automation Paused',
        description: 'Agent execution paused',
      });
    }
  };

  const handleGoalChange = (newGoal: string) => {
    setSession(prev => ({ ...prev, goal: newGoal }));
  };

  const handleBlockInputToggle = (enabled: boolean) => {
    setSession(prev => ({ ...prev, blockInput: enabled }));
  };

  const sessionActive = ['planning', 'executing', 'paused'].includes(session.status);

  return (
    <div className="flex flex-col h-screen bg-[#0f0f10] overflow-hidden">
      {/* Page Header */}
      <div className="px-4 md:px-6 py-3 md:py-4 border-b border-gray-800 flex-shrink-0 bg-[#0f0f10]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 md:gap-4">
            {onClose && (
              <button
                onClick={onClose}
                className="px-2 md:px-4 py-1.5 md:py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors flex items-center gap-1 md:gap-2 text-sm md:text-base"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                <span className="hidden sm:inline">Back</span>
              </button>
            )}
            <div>
              <h1 className="text-base md:text-xl font-bold text-gray-200">Browser Automation</h1>
              <p className="text-xs md:text-sm text-gray-500 mt-0.5 md:mt-1 hidden sm:block">AI-powered browser automation</p>
            </div>
          </div>
          {session.result && (
            <div className={`px-4 py-2 rounded-lg border ${
              session.result.success
                ? 'bg-green-900/20 border-green-700 text-green-400'
                : 'bg-red-900/20 border-red-700 text-red-400'
            }`}>
              <p className="text-sm font-medium">{session.result.message}</p>
              {session.result.payload && (
                <p className="text-xs mt-1 opacity-75">
                  {session.result.completedSteps} / {session.result.totalSteps} steps completed
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Controls */}
      <div className="px-4 md:px-6 py-3 md:py-4 border-b border-gray-800 flex-shrink-0">
        <Controls
          goal={session.goal}
          onGoalChange={handleGoalChange}
          onStart={handleStart}
          onAbort={handleAbort}
          onPauseResume={handlePauseResume}
          sessionActive={sessionActive}
          blockInput={session.blockInput}
          onBlockInputToggle={handleBlockInputToggle}
          status={session.status}
          isPaused={isPaused}
        />
      </div>

      {/* Main Content Area: Viewport + Log */}
      <div className="flex-1 px-4 md:px-6 py-4 md:py-6 overflow-y-auto min-h-0">
        <div className="flex flex-col lg:flex-row gap-3 md:gap-4 h-full">
          {/* Browser Viewport (Full width on mobile, 60% on desktop) */}
          <div className="flex-1 min-w-0 min-h-[250px] md:min-h-[400px]">
            <BrowserViewport
              browserState={session.browserState}
              status={session.status}
            />
          </div>

          {/* Agent Log (Full width on mobile, 40% on desktop) */}
          <div className="w-full lg:w-2/5 min-w-0 min-h-[250px] md:min-h-[400px]">
            <AgentLog
              steps={session.logEntries}
              goal={session.goal}
              currentSubtask={
                session.plan && session.currentStepIndex >= 0
                  ? session.plan.steps[session.currentStepIndex]?.targetDescription
                  : undefined
              }
            />
          </div>
        </div>
      </div>

      {/* User Input Request Modal (if needed) */}
      {session.requiresUserInput && (
        <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-200 mb-3">
              User Input Required
            </h3>
            <p className="text-sm text-gray-400 mb-4">
              {session.requiresUserInput.question}
            </p>
            {session.requiresUserInput.inputType === 'text' && (
              <input
                type="text"
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-gray-300 focus:border-purple-500 focus:outline-none"
                placeholder="Enter your response..."
              />
            )}
            {session.requiresUserInput.inputType === 'choice' && (
              <div className="space-y-2">
                {session.requiresUserInput.choices?.map((choice, index) => (
                  <button
                    key={index}
                    className="w-full px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-gray-300 text-left"
                  >
                    {choice}
                  </button>
                ))}
              </div>
            )}
            <div className="flex gap-2 mt-4">
              <button className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded text-white">
                Submit
              </button>
              <button className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-gray-300">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AutomationPage;
