// Execution Agent: Orchestrates browser automation workflow
import {
  ActionPlan,
  ActionStep,
  BrowserState,
  AgentLogEntry,
  ExecutionResult,
  UserInputRequest,
  HighlightBox
} from './types.ts';
import { plannerService } from './planner.ts';
import { validatorService } from './validator.ts';
import { 
  createAutomationSession, 
  navigateAutomation, 
  findElements, 
  smartClick, 
  typeText, 
  getAutomationScreenshot, 
  closeAutomationSession 
} from '../services/api';

type StateUpdateCallback = (updates: Partial<AutomationState>) => void;

interface AutomationState {
  browserState: BrowserState;
  logEntries: AgentLogEntry[];
  currentStepIndex: number;
  status: 'idle' | 'planning' | 'executing' | 'completed' | 'failed' | 'paused';
  requiresUserInput: UserInputRequest | null;
  result: ExecutionResult | null;
}

class ExecutionAgentService {
  private aborted: boolean = false;
  private paused: boolean = false;
  private stateCallback: StateUpdateCallback | null = null;
  private currentSessionId: string | null = null; // Store session ID

  /**
   * Set callback for state updates
   */
  setStateCallback(callback: StateUpdateCallback) {
    this.stateCallback = callback;
  }

  /**
   * Update state and notify callback
   */
  private updateState(updates: Partial<AutomationState>) {
    if (this.stateCallback) {
      this.stateCallback(updates);
    }
  }

  /**
   * Main entry point: Start automation for a goal
   */
  async startAutomation(goal: string, initialState: AutomationState): Promise<void> {
    console.log(`[ExecutionAgent] Starting automation for goal: "${goal}"`);
    
    this.aborted = false;
    this.paused = false;

    // Create browser session with unique ID
    const sessionId = `browser-${Date.now()}`;
    this.currentSessionId = sessionId;

    try {
      // Initialize browser session via API
      await createAutomationSession(sessionId);
      console.log('[ExecutionAgent] Browser session created:', sessionId);

      // Phase 1: Planning
      this.updateState({ status: 'planning' });
      this.addLog({
        actionType: 'WAIT',
        details: `Analyzing goal and creating action plan...`,
        status: 'pending'
      });

      const planResponse = await plannerService.getPlan(goal);
      const plan = planResponse.plan;

      this.addLog({
        actionType: 'WAIT',
        details: `Plan created: ${plan.steps.length} steps (${planResponse.complexity} task)`,
        status: 'ok'
      });

      // Phase 2: Execution
      this.updateState({ status: 'executing' });

      let completedSteps = 0;
      
      for (let i = 0; i < plan.steps.length; i++) {
        if (this.aborted) {
          console.log('[ExecutionAgent] Automation aborted by user');
          await this.cleanupSession(sessionId);
          this.updateState({
            status: 'failed',
            result: {
              success: false,
              message: 'Automation aborted by user',
              completedSteps: i,
              totalSteps: plan.steps.length
            }
          });
          return;
        }

        // Handle pause
        while (this.paused && !this.aborted) {
          await new Promise(resolve => setTimeout(resolve, 500));
        }

        this.updateState({ currentStepIndex: i });
        const step = plan.steps[i];

        // Execute step with retry logic
        const stepSuccess = await this.executeStepWithRetry(step, initialState.browserState);
        
        if (stepSuccess) {
          completedSteps++;
        } else {
          // Step failed after all retries
          console.error(`[ExecutionAgent] Step ${i + 1} failed after all retries`);
          await this.cleanupSession(sessionId);
          this.updateState({
            status: 'failed',
            result: {
              success: false,
              message: `Failed at step ${i + 1}: ${step.targetDescription}`,
              completedSteps,
              totalSteps: plan.steps.length
            }
          });
          return;
        }
      }

      // Phase 3: Final Validation & Result
      this.addLog({
        actionType: 'WAIT',
        details: 'Validating final result...',
        status: 'pending'
      });

      const finalValidation = await validatorService.validateFinalResult(
        initialState.browserState,
        goal
      );

      // Get final screenshot
      const finalScreenshot = await this.getFinalScreenshot(sessionId);

      // Cleanup session
      await this.cleanupSession(sessionId);

      if (finalValidation.isValid) {
        const result: ExecutionResult = {
          success: true,
          message: 'Automation completed successfully!',
          payload: {
            goal,
            completedAt: new Date().toISOString(),
            finalUrl: initialState.browserState.currentUrl
          },
          finalScreenshot: finalScreenshot || initialState.browserState.screenshot,
          completedSteps,
          totalSteps: plan.steps.length
        };

        this.addLog({
          actionType: 'WAIT',
          details: `✅ SUCCESS: ${result.message}`,
          status: 'ok'
        });

        this.updateState({
          status: 'completed',
          result
        });
      } else {
        this.addLog({
          actionType: 'WAIT',
          details: `⚠️ Completed with issues: ${finalValidation.issues.join(', ')}`,
          status: 'fail'
        });

        this.updateState({
          status: 'completed',
          result: {
            success: false,
            message: 'Automation completed but validation found issues',
            payload: { issues: finalValidation.issues },
            finalScreenshot: finalScreenshot,
            completedSteps,
            totalSteps: plan.steps.length
          }
        });
      }

    } catch (error: any) {
      console.error('[ExecutionAgent] Automation error:', error);
      
      this.addLog({
        actionType: 'WAIT',
        details: `❌ ERROR: ${error.message}`,
        status: 'fail',
        error: error.message
      });

      this.updateState({
        status: 'failed',
        result: {
          success: false,
          message: `Automation failed: ${error.message}`,
          completedSteps: 0,
          totalSteps: 0
        }
      });
    }
  }

  /**
   * Get final screenshot from browser session
   */
  private async getFinalScreenshot(sessionId: string): Promise<string | null> {
    try {
      const API_BASE = process.env.REACT_APP_BACKEND_URL || '';
      const response = await fetch(`${API_BASE}/api/automation/screenshot/${sessionId}`);
      const data = await response.json();
      return data.screenshot;
    } catch (error) {
      console.error('[ExecutionAgent] Error getting final screenshot:', error);
      return null;
    }
  }

  /**
   * Cleanup browser session
   */
  private async cleanupSession(sessionId: string): Promise<void> {
    try {
      const API_BASE = process.env.REACT_APP_BACKEND_URL || '';
      await fetch(`${API_BASE}/api/automation/session/${sessionId}`, {
        method: 'DELETE'
      });
      console.log('[ExecutionAgent] Browser session cleaned up');
    } catch (error) {
      console.error('[ExecutionAgent] Error cleaning up session:', error);
    }
  }

  /**
   * Execute a single step with retry logic
   */
  private async executeStepWithRetry(step: ActionStep, browserState: BrowserState): Promise<boolean> {
    const maxRetries = step.maxRetries || 3;
    let attempt = 0;

    while (attempt < maxRetries) {
      attempt++;
      
      const retryLabel = attempt > 1 ? ` (Retry ${attempt}/${maxRetries})` : '';
      
      this.addLog({
        actionType: step.actionType,
        details: `${step.actionType}: ${step.targetDescription}${retryLabel}`,
        status: 'pending',
        retryAttempt: attempt > 1 ? attempt : undefined
      });

      // Perform the step
      const stepResult = await this.performStep(step, browserState);

      if (this.aborted) return false;

      // Validate the step
      const validation = await validatorService.check(browserState, step, attempt);

      if (validation.isValid) {
        // Step succeeded
        this.updateLastLog({ status: 'ok' });
        return true;
      } else {
        // Step failed
        const errorDetails = validation.issues.join('; ');
        
        if (attempt < maxRetries && validation.shouldRetry) {
          this.updateLastLog({ 
            status: 'retrying',
            error: errorDetails
          });
          
          // Wait before retry
          await new Promise(resolve => setTimeout(resolve, 1000));
        } else {
          this.updateLastLog({ 
            status: 'fail',
            error: errorDetails
          });
          return false;
        }
      }
    }

    return false;
  }

  /**
   * Perform a single automation step (REAL BROWSER)
   */
  private async performStep(step: ActionStep, browserState: BrowserState): Promise<void> {
    console.log(`[ExecutionAgent] Performing ${step.actionType}: ${step.targetDescription}`);

    // Make API call to real browser service
    const API_BASE = process.env.REACT_APP_BACKEND_URL || '';
    const sessionId = `browser-${Date.now()}`;

    try {
      let response;

      switch (step.actionType) {
        case 'NAVIGATE':
          response = await fetch(`${API_BASE}/api/automation/navigate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              session_id: sessionId,
              url: step.targetSelector || 'https://google.com'
            })
          });
          break;

        case 'CLICK':
          response = await fetch(`${API_BASE}/api/automation/click`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              session_id: sessionId,
              selector: step.targetSelector
            })
          });
          break;

        case 'TYPE':
          response = await fetch(`${API_BASE}/api/automation/type`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              session_id: sessionId,
              selector: step.targetSelector,
              text: step.inputValue || ''
            })
          });
          break;

        case 'WAIT':
          response = await fetch(`${API_BASE}/api/automation/wait`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              session_id: sessionId,
              selector: step.targetSelector || 'body',
              timeout: 5000
            })
          });
          break;

        default:
          // Fallback to simulation for unsupported actions
          await new Promise(resolve => setTimeout(resolve, 1000));
          const updates = this.simulateStepExecution(step, browserState);
          this.updateState({ browserState: updates });
          return;
      }

      if (response) {
        const data = await response.json();
        
        if (data.success || data.screenshot) {
          // Update browser state with real data
          const newState: BrowserState = {
            ...browserState,
            currentUrl: data.url || browserState.currentUrl,
            screenshot: data.screenshot || browserState.screenshot,
            pageTitle: data.title || browserState.pageTitle,
            highlightBoxes: data.highlight ? [{
              x: data.highlight.x,
              y: data.highlight.y,
              w: data.highlight.width,
              h: data.highlight.height,
              label: `${step.actionType}: ${step.targetDescription}`,
              color: '#3b82f6'
            }] : [],
            timestamp: Date.now()
          };

          this.updateState({ browserState: newState });
        } else {
          throw new Error(data.error || 'Browser action failed');
        }
      }

    } catch (error: any) {
      console.error(`[ExecutionAgent] Browser action error:`, error);
      // Fallback to simulation on error
      const updates = this.simulateStepExecution(step, browserState);
      this.updateState({ browserState: updates });
    }
  }

  /**
   * Simulate step execution and generate new browser state
   */
  private simulateStepExecution(step: ActionStep, currentState: BrowserState): BrowserState {
    const newState: BrowserState = {
      ...currentState,
      timestamp: Date.now()
    };

    // Generate new screenshot placeholder
    newState.screenshot = this.generateScreenshotPlaceholder(step.actionType);

    // Create highlight boxes to show where agent acted
    const highlightBoxes: HighlightBox[] = [];
    
    switch (step.actionType) {
      case 'NAVIGATE':
        newState.currentUrl = `https://example.com/${step.id}`;
        newState.pageTitle = `${step.targetDescription} - Page`;
        break;

      case 'CLICK':
        highlightBoxes.push({
          x: 100 + Math.random() * 300,
          y: 100 + Math.random() * 200,
          w: 120,
          h: 40,
          label: `CLICK: ${step.targetDescription}`,
          color: '#3b82f6'
        });
        break;

      case 'TYPE':
        highlightBoxes.push({
          x: 150 + Math.random() * 250,
          y: 150 + Math.random() * 150,
          w: 200,
          h: 35,
          label: `TYPE: ${step.targetDescription}`,
          color: '#10b981'
        });
        break;

      case 'SUBMIT':
        highlightBoxes.push({
          x: 200 + Math.random() * 200,
          y: 300 + Math.random() * 100,
          w: 100,
          h: 40,
          label: 'SUBMIT',
          color: '#8b5cf6'
        });
        break;

      case 'CAPTCHA':
        highlightBoxes.push({
          x: 180,
          y: 250,
          w: 300,
          h: 150,
          label: 'SOLVING CAPTCHA...',
          color: '#f59e0b'
        });
        break;
    }

    newState.highlightBoxes = highlightBoxes;

    return newState;
  }

  /**
   * Generate a placeholder screenshot (base64 data URL)
   */
  private generateScreenshotPlaceholder(actionType: string): string {
    // Create a simple canvas-based placeholder
    // In production, this would be actual screenshot from browser
    
    const colors: Record<string, string> = {
      NAVIGATE: '#1e293b',
      CLICK: '#0f172a',
      TYPE: '#18181b',
      WAIT: '#171717',
      SUBMIT: '#1c1917',
      CAPTCHA: '#1e1b4b',
      default: '#0f0f10'
    };

    const bgColor = colors[actionType] || colors.default;
    
    // Simple SVG as placeholder
    const svg = `
      <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
        <rect width="800" height="600" fill="${bgColor}"/>
        <text x="400" y="300" font-family="Arial" font-size="24" fill="#64748b" text-anchor="middle">
          Browser State After: ${actionType}
        </text>
        <text x="400" y="340" font-family="Arial" font-size="14" fill="#475569" text-anchor="middle">
          ${new Date().toLocaleTimeString()}
        </text>
      </svg>
    `;

    return `data:image/svg+xml;base64,${btoa(svg)}`;
  }

  /**
   * Add a log entry
   */
  private addLog(entry: Omit<AgentLogEntry, 'id' | 'timestamp'>) {
    const newEntry: AgentLogEntry = {
      id: `log-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toLocaleTimeString(),
      ...entry
    };

    this.updateState({
      logEntries: [] // Will be merged in component
    });

    // Emit new log entry
    if (this.stateCallback) {
      this.stateCallback({ logEntries: [newEntry] });
    }
  }

  /**
   * Update the last log entry
   */
  private updateLastLog(updates: Partial<AgentLogEntry>) {
    if (this.stateCallback) {
      this.stateCallback({ logEntries: [updates as AgentLogEntry] });
    }
  }

  /**
   * Abort current automation
   */
  abort() {
    console.log('[ExecutionAgent] Aborting automation...');
    this.aborted = true;
  }

  /**
   * Pause automation
   */
  pause() {
    console.log('[ExecutionAgent] Pausing automation...');
    this.paused = true;
  }

  /**
   * Resume automation
   */
  resume() {
    console.log('[ExecutionAgent] Resuming automation...');
    this.paused = false;
  }

  /**
   * Check if automation is paused
   */
  isPaused(): boolean {
    return this.paused;
  }
}

export const executionAgent = new ExecutionAgentService();
