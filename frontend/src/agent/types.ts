// Agent Types and Interfaces for Browser Automation

export type ActionType = 
  | 'NAVIGATE' 
  | 'CLICK' 
  | 'TYPE' 
  | 'WAIT' 
  | 'SCROLL'
  | 'CAPTCHA'
  | 'CAPTCHA_CHALLENGE'
  | 'SELECT'
  | 'SUBMIT'
  | 'SMART_CLICK'
  | 'SMART_TYPE';

export type StepStatus = 'pending' | 'ok' | 'fail' | 'retrying' | 'needs_human';

export interface ActionStep {
  id: string;
  actionType: ActionType;
  targetDescription: string;
  targetSelector?: string;
  targetHint?: string; // Natural language hint for SMART actions
  inputValue?: string;
  expectedOutcome: string;
  retryCount?: number;
  maxRetries?: number;
}

export interface ActionPlan {
  goal: string;
  steps: ActionStep[];
  estimatedDuration?: number;
  confidence?: number; // Planner confidence in plan
  concerns?: string[]; // Planner concerns/warnings
}

export interface HighlightBox {
  x: number;
  y: number;
  w: number;
  h: number;
  label: string;
  color?: string;
}

export interface BrowserState {
  currentUrl: string;
  screenshot: string; // base64 dataURL
  highlightBoxes: HighlightBox[];
  pageTitle: string;
  timestamp: number;
}

export interface AgentLogEntry {
  id: string;
  timestamp: string;
  actionType: ActionType;
  details: string;
  status: StepStatus;
  retryAttempt?: number;
  error?: string;
  confidence?: number;
  concerns?: string[];
  needsHuman?: boolean;
}

export interface ExecutionResult {
  success: boolean;
  message: string;
  payload?: Record<string, any>; // Credentials, final data, etc.
  finalScreenshot?: string;
  completedSteps: number;
  totalSteps: number;
}

export interface UserInputRequest {
  id: string;
  question: string;
  inputType: 'text' | 'number' | 'password' | 'choice';
  choices?: string[];
  required: boolean;
}

export interface AutomationSession {
  sessionId: string;
  goal: string;
  plan: ActionPlan | null;
  browserState: BrowserState;
  logEntries: AgentLogEntry[];
  status: 'idle' | 'planning' | 'executing' | 'completed' | 'failed' | 'paused' | 'needs_human';
  currentStepIndex: number;
  blockInput: boolean;
  requiresUserInput: UserInputRequest | null;
  result: ExecutionResult | null;
  startTime?: number;
  endTime?: number;
  controlMode?: 'manual' | 'agent' | 'paused'; // Control mode for UI
}

export interface PlannerResponse {
  plan: ActionPlan;
  complexity: 'simple' | 'moderate' | 'complex';
  estimatedSteps: number;
  confidence?: number;
  concerns?: string[];
}

export interface ValidatorResponse {
  isValid: boolean;
  confidence: number;
  issues: string[];
  shouldRetry: boolean;
  suggestions?: string[];
  needsHuman?: boolean;
  concerns?: string[];
}

// Unified Step Result (backend format)
export interface UnifiedStepResult {
  success: boolean;
  confidence: number;
  concerns: string[];
  needs_human: boolean;
  step_name: string;
  screenshot_after?: string;
  timestamp: string;
  details?: Record<string, any>;
}

