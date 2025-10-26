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
      
      console.log('[ExecutionAgent] ✅ Plan received:', plan);
      console.log('[ExecutionAgent] Plan has', plan.steps?.length || 0, 'steps');
      console.log('[ExecutionAgent] Steps:', plan.steps);

      if (!plan || !plan.steps || plan.steps.length === 0) {
        console.error('[ExecutionAgent] ❌ ERROR: Plan has no steps!');
        this.addLog({
          actionType: 'WAIT',
          details: 'ERROR: Failed to generate plan - no steps created',
          status: 'error'
        });
        await this.cleanupSession(sessionId);
        this.updateState({
          status: 'failed',
          result: {
            success: false,
            message: 'Generated plan has no steps',
            completedSteps: 0,
            totalSteps: 0
          }
        });
        return;
      }

      this.addLog({
        actionType: 'WAIT',
        details: `Plan created: ${plan.steps.length} steps (${planResponse.complexity} task)`,
        status: 'ok'
      });

      // Phase 2: Execution
      console.log('[ExecutionAgent] 🚀 Starting execution phase...');
      this.updateState({ status: 'executing' });

      let completedSteps = 0;
      
      console.log('[ExecutionAgent] Entering execution loop for', plan.steps.length, 'steps');
      
      for (let i = 0; i < plan.steps.length; i++) {
        console.log(`[ExecutionAgent] 📍 Loop iteration ${i + 1}/${plan.steps.length}`);
        
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

        console.log(`[ExecutionAgent] Updating current step index to ${i}`);
        this.updateState({ currentStepIndex: i });
        const step = plan.steps[i];
        
        console.log(`[ExecutionAgent] Executing step: ${step.actionType} - ${step.targetDescription}`);

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
      await closeAutomationSession(sessionId);
      console.log('[ExecutionAgent] Browser session cleaned up');
      this.currentSessionId = null;
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
   * Perform a single automation step (REAL BROWSER via API)
   */
  private async performStep(step: ActionStep, browserState: BrowserState): Promise<void> {
    console.log(`[ExecutionAgent] Performing ${step.actionType}: ${step.targetDescription}`);
    console.log(`[ExecutionAgent] Current session ID: ${this.currentSessionId}`);

    if (!this.currentSessionId) {
      const error = 'No active browser session - session ID is null';
      console.error(`[ExecutionAgent] ERROR: ${error}`);
      throw new Error(error);
    }

    try {
      let result;

      switch (step.actionType) {
        case 'NAVIGATE':
          // Navigate to URL
          const navUrl = step.targetSelector || step.inputValue || 'https://google.com';
          console.log(`[ExecutionAgent] Navigating to: ${navUrl}`);
          
          result = await navigateAutomation(this.currentSessionId, navUrl);
          console.log(`[ExecutionAgent] Navigation result:`, result);
          
          // Update browser state with screenshot
          if (result.screenshot) {
            const newState: BrowserState = {
              ...browserState,
              currentUrl: result.url || navUrl,
              screenshot: result.screenshot,
              pageTitle: result.title || 'Page',
              highlightBoxes: [],
              timestamp: Date.now()
            };
            this.updateState({ browserState: newState });
            console.log(`[ExecutionAgent] Browser state updated with screenshot`);
          } else {
            console.warn(`[ExecutionAgent] No screenshot in navigation result`);
          }
          break;

        case 'CLICK':
          // Use smart-click with vision model
          console.log(`[ExecutionAgent] Smart clicking: ${step.targetDescription}`);
          
          result = await smartClick(this.currentSessionId, step.targetDescription);
          console.log(`[ExecutionAgent] Click result:`, result);
          
          // Update with new screenshot after click
          if (result.screenshot) {
            const newState: BrowserState = {
              ...browserState,
              screenshot: result.screenshot,
              highlightBoxes: result.box ? [{
                x: result.box.x,
                y: result.box.y,
                w: result.box.width,
                h: result.box.height,
                label: `Clicked: ${step.targetDescription}`,
                color: '#22c55e'
              }] : [],
              timestamp: Date.now()
            };
            this.updateState({ browserState: newState });
            console.log(`[ExecutionAgent] State updated after click`);
          }
          break;

        case 'TYPE':
          // Type text into element
          const textToType = step.inputValue || '';
          console.log(`[ExecutionAgent] Typing into ${step.targetDescription}: ${textToType}`);
          
          result = await typeText(
            this.currentSessionId, 
            step.targetDescription, 
            textToType
          );
          console.log(`[ExecutionAgent] Type result:`, result);
          
          // Update with screenshot
          if (result.screenshot) {
            const newState: BrowserState = {
              ...browserState,
              screenshot: result.screenshot,
              highlightBoxes: result.box ? [{
                x: result.box.x,
                y: result.box.y,
                w: result.box.width,
                h: result.box.height,
                label: `Typed: "${textToType}"`,
                color: '#3b82f6'
              }] : [],
              timestamp: Date.now()
            };
            this.updateState({ browserState: newState });
            console.log(`[ExecutionAgent] State updated after typing`);
          }
          break;

        case 'WAIT':
          // Simple wait (no API call needed)
          console.log(`[ExecutionAgent] Waiting 2 seconds...`);
          await new Promise(resolve => setTimeout(resolve, 2000));
          
          // Get fresh screenshot
          console.log(`[ExecutionAgent] Getting fresh screenshot after wait`);
          const screenshot = await getAutomationScreenshot(this.currentSessionId);
          
          if (screenshot.screenshot) {
            const newState: BrowserState = {
              ...browserState,
              screenshot: screenshot.screenshot,
              timestamp: Date.now()
            };
            this.updateState({ browserState: newState });
            console.log(`[ExecutionAgent] Screenshot updated after wait`);
          }
          break;

        case 'CAPTCHA':
          // Handle captcha with vision model
          console.log(`[ExecutionAgent] Attempting to solve captcha`);
          
          // First, find the captcha element
          try {
            const elements = await findElements(this.currentSessionId, 'captcha element or checkbox');
            console.log(`[ExecutionAgent] Found ${elements.elements?.length || 0} captcha elements`);
            
            if (elements.elements && elements.elements.length > 0) {
              // Click the first captcha element
              result = await smartClick(this.currentSessionId, 'captcha');
              
              if (result.screenshot) {
                const newState: BrowserState = {
                  ...browserState,
                  screenshot: result.screenshot,
                  timestamp: Date.now()
                };
                this.updateState({ browserState: newState });
                console.log(`[ExecutionAgent] Captcha clicked, state updated`);
              }
            }
          } catch (captchaError) {
            console.warn(`[ExecutionAgent] Captcha handling warning:`, captchaError);
            // Continue anyway - captcha might not be present
          }
          break;

        default:
          console.warn(`[ExecutionAgent] Unsupported action type: ${step.actionType}`);
          // Get current screenshot for unsupported actions
          const fallbackScreenshot = await getAutomationScreenshot(this.currentSessionId);
          if (fallbackScreenshot.screenshot) {
            const newState: BrowserState = {
              ...browserState,
              screenshot: fallbackScreenshot.screenshot,
              timestamp: Date.now()
            };
            this.updateState({ browserState: newState });
          }
      }

      console.log(`[ExecutionAgent] Step completed successfully: ${step.actionType}`);

    } catch (error: any) {
      console.error(`[ExecutionAgent] Browser action error:`, error);
      console.error(`[ExecutionAgent] Error details:`, {
        step: step.actionType,
        sessionId: this.currentSessionId,
        message: error.message,
        stack: error.stack
      });
      throw error; // Propagate error for retry logic
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
