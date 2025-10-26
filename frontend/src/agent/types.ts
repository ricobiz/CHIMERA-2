// Agent Types and Interfaces for Browser Automation

export type ActionType = 
  | 'NAVIGATE' 
  | 'CLICK' 
  | 'TYPE' 
  | 'WAIT' 
  | 'SCROLL'
  | 'CAPTCHA'
  | 'SELECT'
  | 'SUBMIT';

export type StepStatus = 'pending' | 'ok' | 'fail' | 'retrying';

export interface ActionStep {
  id: string;
  actionType: ActionType;
  targetDescription: string;
  targetSelector?: string;
  inputValue?: string;
  expectedOutcome: string;
  retryCount?: number;
  maxRetries?: number;
}

export interface ActionPlan {
  goal: string;
  steps: ActionStep[];
  estimatedDuration?: number;
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
  status: 'idle' | 'planning' | 'executing' | 'completed' | 'failed' | 'paused';
  currentStepIndex: number;
  blockInput: boolean;
  requiresUserInput: UserInputRequest | null;
  result: ExecutionResult | null;
  startTime?: number;
  endTime?: number;
}

export interface PlannerResponse {
  plan: ActionPlan;
  complexity: 'simple' | 'moderate' | 'complex';
  estimatedSteps: number;
}

export interface ValidatorResponse {
  isValid: boolean;
  confidence: number;
  issues: string[];
  shouldRetry: boolean;
  suggestions?: string[];
}
