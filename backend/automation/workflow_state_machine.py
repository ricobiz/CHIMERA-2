"""
Workflow State Machine - Tracks and manages workflow states during automation
Provides intelligent state determination and validation for adaptive orchestration
"""

import logging
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from services.openrouter_service import openrouter_service

logger = logging.getLogger(__name__)


class WorkflowState(Enum):
    """States in autonomous automation workflow"""
    INITIAL = "initial"
    ANALYZING_SITE = "analyzing_site"
    LOCATING_ENTRY = "locating_entry"
    FORM_DETECTED = "form_detected"
    FILLING_FORM = "filling"
    HANDLING_CAPTCHA = "captcha"
    SUBMITTING = "submitting"
    WAITING_RESPONSE = "waiting"
    EMAIL_VERIFICATION = "email_verify"
    PHONE_VERIFICATION = "phone_verify"
    TWO_FACTOR_AUTH = "2fa"
    AUTHENTICATED = "authenticated"
    ERROR_STATE = "error"
    STUCK_STATE = "stuck"
    GOAL_ACHIEVED = "achieved"
    GOAL_FAILED = "failed"


class WorkflowStateMachine:
    """Manages workflow state transitions and validation for intelligent orchestration"""
    
    def __init__(self):
        self.current_state = WorkflowState.INITIAL
        self.state_history: List[Dict[str, Any]] = []
        self.state_metadata: Dict[str, Any] = {}
    
    async def determine_state(
        self, 
        perception: Dict[str, Any], 
        previous_state: WorkflowState,
        goal: str = ""
    ) -> WorkflowState:
        """
        Intelligently determine current workflow state based on page analysis.
        Uses heuristics + LLM for complex cases.
        
        Args:
            perception: Current page perception data
            previous_state: Previous workflow state
            goal: Original automation goal
            
        Returns:
            Determined workflow state
        """
        try:
            url = perception.get('url', '').lower()
            page_type = perception.get('page_analysis', {}).get('page_type', 'unknown')
            page_text = perception.get('page_text', '').lower()
            errors = perception.get('page_analysis', {}).get('errors', [])
            success_msgs = perception.get('page_analysis', {}).get('success_messages', [])
            forms = perception.get('page_analysis', {}).get('forms', [])
            
            # Priority 1: Goal achievement indicators
            if success_msgs or page_type in ["dashboard", "success_page"]:
                return WorkflowState.AUTHENTICATED
            
            # Priority 2: Verification requirements
            if "verify" in page_text and "email" in page_text:
                return WorkflowState.EMAIL_VERIFICATION
            
            if "verify" in page_text and ("phone" in page_text or "sms" in page_text):
                return WorkflowState.PHONE_VERIFICATION
            
            # Priority 3: Error and blocking states
            if any("captcha" in e.lower() for e in errors) or "captcha" in page_text or "hcaptcha" in page_text or "recaptcha" in page_text:
                return WorkflowState.HANDLING_CAPTCHA
            
            if errors and previous_state in [WorkflowState.ERROR_STATE, WorkflowState.STUCK_STATE]:
                # Repeated errors indicate stuck state
                return WorkflowState.STUCK_STATE
            
            if errors:
                return WorkflowState.ERROR_STATE
            
            # Priority 4: Form interaction states
            if forms and page_type in ["registration", "login", "form"]:
                # Check if we're actively filling or just detected
                if previous_state == WorkflowState.FILLING_FORM:
                    return WorkflowState.FILLING_FORM
                else:
                    return WorkflowState.FORM_DETECTED
            
            # Priority 5: Navigation states
            if "/register" in url or "/signup" in url or page_type == "registration":
                if previous_state in [WorkflowState.FILLING_FORM, WorkflowState.SUBMITTING]:
                    return previous_state
                return WorkflowState.FORM_DETECTED
            
            if "/login" in url or page_type == "login":
                if previous_state in [WorkflowState.FILLING_FORM, WorkflowState.SUBMITTING]:
                    return previous_state
                return WorkflowState.FORM_DETECTED
            
            # Priority 6: Loading/waiting states
            if "loading" in page_text or "please wait" in page_text:
                return WorkflowState.WAITING_RESPONSE
            
            # Priority 7: Use LLM for ambiguous cases
            if previous_state in [WorkflowState.INITIAL, WorkflowState.ANALYZING_SITE]:
                return await self._llm_state_determination(perception, previous_state, goal)
            
            # Default: maintain previous state if unclear
            return previous_state
            
        except Exception as e:
            logger.error(f"❌ [STATE_MACHINE] State determination failed: {e}")
            return previous_state
    
    async def _llm_state_determination(
        self, 
        perception: Dict[str, Any], 
        previous_state: WorkflowState,
        goal: str
    ) -> WorkflowState:
        """Use LLM to determine state in ambiguous cases"""
        try:
            prompt = f"""
Determine the current workflow state for this automation:

**Goal:** {goal}
**Previous State:** {previous_state.value}

**Current Page:**
- URL: {perception.get('url', 'unknown')}
- Page Type: {perception.get('page_analysis', {}).get('page_type', 'unknown')}
- Has Forms: {len(perception.get('page_analysis', {}).get('forms', [])) > 0}
- Errors: {perception.get('page_analysis', {}).get('errors', [])}
- Success Messages: {perception.get('page_analysis', {}).get('success_messages', [])}

**Page Text (first 300 chars):**
{perception.get('page_text', '')[:300]}

Based on the page state, what workflow state are we in?

Return ONLY one of these states:
- initial: Just started, need to locate entry point
- locating_entry: Looking for registration/login form
- form_detected: Found the target form
- filling: Currently filling out form fields
- submitting: Form submitted, waiting for response
- email_verify: Email verification required
- phone_verify: Phone verification required
- authenticated: Successfully logged in/registered
- error: Error encountered but recoverable
- stuck: Stuck and need replanning

Return only the state name, nothing else.
"""
            
            messages = [
                {"role": "system", "content": "You are an expert at analyzing web automation workflow states. Return only the state name."},
                {"role": "user", "content": prompt}
            ]
            
            response = await openrouter_service.chat_completion(
                messages=messages,
                model="qwen/qwen2.5-72b-instruct",
                temperature=0.1,
                max_tokens=50
            )
            
            state_str = response['choices'][0]['message']['content'].strip().lower()
            
            # Map response to enum
            state_mapping = {
                "initial": WorkflowState.INITIAL,
                "locating_entry": WorkflowState.LOCATING_ENTRY,
                "form_detected": WorkflowState.FORM_DETECTED,
                "filling": WorkflowState.FILLING_FORM,
                "submitting": WorkflowState.SUBMITTING,
                "email_verify": WorkflowState.EMAIL_VERIFICATION,
                "phone_verify": WorkflowState.PHONE_VERIFICATION,
                "authenticated": WorkflowState.AUTHENTICATED,
                "error": WorkflowState.ERROR_STATE,
                "stuck": WorkflowState.STUCK_STATE
            }
            
            return state_mapping.get(state_str, previous_state)
            
        except Exception as e:
            logger.error(f"❌ [STATE_MACHINE] LLM state determination failed: {e}")
            return previous_state
    
    def get_valid_transitions(self, current_state: WorkflowState) -> List[WorkflowState]:
        """Get list of valid next states from current state"""
        transitions = {
            WorkflowState.INITIAL: [
                WorkflowState.ANALYZING_SITE, 
                WorkflowState.LOCATING_ENTRY,
                WorkflowState.FORM_DETECTED
            ],
            WorkflowState.ANALYZING_SITE: [
                WorkflowState.LOCATING_ENTRY, 
                WorkflowState.FORM_DETECTED
            ],
            WorkflowState.LOCATING_ENTRY: [
                WorkflowState.FORM_DETECTED, 
                WorkflowState.ERROR_STATE
            ],
            WorkflowState.FORM_DETECTED: [
                WorkflowState.FILLING_FORM, 
                WorkflowState.HANDLING_CAPTCHA,
                WorkflowState.ERROR_STATE
            ],
            WorkflowState.FILLING_FORM: [
                WorkflowState.SUBMITTING, 
                WorkflowState.ERROR_STATE, 
                WorkflowState.HANDLING_CAPTCHA,
                WorkflowState.FILLING_FORM  # Can stay in filling
            ],
            WorkflowState.HANDLING_CAPTCHA: [
                WorkflowState.FILLING_FORM, 
                WorkflowState.STUCK_STATE,
                WorkflowState.SUBMITTING
            ],
            WorkflowState.SUBMITTING: [
                WorkflowState.WAITING_RESPONSE, 
                WorkflowState.ERROR_STATE,
                WorkflowState.AUTHENTICATED
            ],
            WorkflowState.WAITING_RESPONSE: [
                WorkflowState.EMAIL_VERIFICATION, 
                WorkflowState.PHONE_VERIFICATION, 
                WorkflowState.AUTHENTICATED, 
                WorkflowState.ERROR_STATE,
                WorkflowState.TWO_FACTOR_AUTH
            ],
            WorkflowState.EMAIL_VERIFICATION: [
                WorkflowState.AUTHENTICATED, 
                WorkflowState.WAITING_RESPONSE,
                WorkflowState.STUCK_STATE
            ],
            WorkflowState.PHONE_VERIFICATION: [
                WorkflowState.STUCK_STATE,  # Requires human
                WorkflowState.AUTHENTICATED
            ],
            WorkflowState.TWO_FACTOR_AUTH: [
                WorkflowState.STUCK_STATE,
                WorkflowState.AUTHENTICATED
            ],
            WorkflowState.ERROR_STATE: [
                WorkflowState.FORM_DETECTED, 
                WorkflowState.FILLING_FORM,
                WorkflowState.STUCK_STATE,
                WorkflowState.LOCATING_ENTRY
            ],
            WorkflowState.STUCK_STATE: [
                WorkflowState.GOAL_FAILED,
                WorkflowState.LOCATING_ENTRY,  # After replanning
                WorkflowState.FORM_DETECTED
            ],
            WorkflowState.AUTHENTICATED: [
                WorkflowState.GOAL_ACHIEVED
            ],
        }
        return transitions.get(current_state, [])
    
    def transition_to(self, new_state: WorkflowState, metadata: Dict[str, Any] = None):
        """Transition to new state with validation"""
        valid_transitions = self.get_valid_transitions(self.current_state)
        
        if new_state not in valid_transitions and new_state != self.current_state:
            logger.warning(
                f"⚠️ [STATE_MACHINE] Unusual transition: {self.current_state.value} -> {new_state.value}"
            )
        
        self.state_history.append({
            "from": self.current_state.value,
            "to": new_state.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {}
        })
        
        logger.info(f"🔄 [STATE_MACHINE] State transition: {self.current_state.value} → {new_state.value}")
        
        self.current_state = new_state
        self.state_metadata = metadata or {}
    
    def is_terminal_state(self, state: Optional[WorkflowState] = None) -> bool:
        """Check if state is terminal (goal achieved or failed)"""
        check_state = state if state is not None else self.current_state
        return check_state in [
            WorkflowState.GOAL_ACHIEVED, 
            WorkflowState.GOAL_FAILED
        ]
    
    def is_blocked_state(self, state: Optional[WorkflowState] = None) -> bool:
        """Check if state requires human intervention"""
        check_state = state if state is not None else self.current_state
        return check_state in [
            WorkflowState.PHONE_VERIFICATION,
            WorkflowState.TWO_FACTOR_AUTH,
            WorkflowState.STUCK_STATE
        ]
    
    def get_state_description(self, state: Optional[WorkflowState] = None) -> str:
        """Get human-readable description of state"""
        check_state = state if state is not None else self.current_state
        
        descriptions = {
            WorkflowState.INITIAL: "Starting automation workflow",
            WorkflowState.ANALYZING_SITE: "Analyzing target website",
            WorkflowState.LOCATING_ENTRY: "Locating registration/login entry point",
            WorkflowState.FORM_DETECTED: "Found target form on page",
            WorkflowState.FILLING_FORM: "Filling out form fields",
            WorkflowState.HANDLING_CAPTCHA: "Solving CAPTCHA challenge",
            WorkflowState.SUBMITTING: "Submitting form data",
            WorkflowState.WAITING_RESPONSE: "Waiting for server response",
            WorkflowState.EMAIL_VERIFICATION: "Email verification required",
            WorkflowState.PHONE_VERIFICATION: "Phone verification required (needs human)",
            WorkflowState.TWO_FACTOR_AUTH: "2FA required (needs human)",
            WorkflowState.AUTHENTICATED: "Successfully authenticated",
            WorkflowState.ERROR_STATE: "Error encountered, attempting recovery",
            WorkflowState.STUCK_STATE: "Automation stuck, needs replanning",
            WorkflowState.GOAL_ACHIEVED: "Goal successfully achieved!",
            WorkflowState.GOAL_FAILED: "Goal failed, cannot proceed"
        }
        
        return descriptions.get(check_state, "Unknown state")
    
    def get_state_history_summary(self) -> List[Dict[str, Any]]:
        """Get summary of state transitions"""
        return self.state_history.copy()
    
    def reset(self):
        """Reset state machine to initial state"""
        self.current_state = WorkflowState.INITIAL
        self.state_history = []
        self.state_metadata = {}


# Global instance
workflow_state_machine = WorkflowStateMachine()
