"""
Autonomous Agent - Main Orchestrator for Chimera AIOS Automation
Implements bulletproof automation with meta-reasoning, tool orchestration, and recovery
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable
from enum import Enum

from automation.meta_planner import MetaPlanner
from automation.tactical_brain import TacticalBrain 
from automation.tools.orchestrator import ToolOrchestrator
from automation.perception import Perception
from automation.execution import Execution
from automation.verification import Verification
from automation.workflow_state_machine import WorkflowStateMachine, WorkflowState
from services.browser_automation_service import browser_service
from services.head_brain_service import head_brain_service
from services.planner_service import planner_service

logger = logging.getLogger(__name__)

class AgentState(Enum):
    IDLE = "idle"
    ANALYZING = "analyzing"
    PLANNING = "planning" 
    EXECUTING = "executing"
    STUCK = "stuck"
    META_REASONING = "meta_reasoning"
    WAITING_USER = "waiting_user"
    COMPLETED = "completed"
    FAILED = "failed"

class AutonomousAgent:
    """
    Main autonomous agent that orchestrates all automation components.
    Designed for maximum reliability and adaptability.
    """
    
    def __init__(self, websocket_callback: Optional[Callable] = None):
        # Communication
        self.ws_callback = websocket_callback
        
        # Core components
        self.meta_planner = MetaPlanner()
        self.tactical = TacticalBrain()
        self.tools = ToolOrchestrator()
        self.perception = Perception()
        self.execution = Execution()
        self.verification = Verification()
        self.state_machine = WorkflowStateMachine()  # NEW: Workflow state tracking
        
        # State
        self.state = AgentState.IDLE
        self.session_id: Optional[str] = None
        self.task_id: Optional[str] = None
        self.current_goal: str = ""
        self.previous_workflow_state: WorkflowState = WorkflowState.INITIAL  # NEW: Track previous state
        
        # Resources and data
        self.resources: Dict[str, Any] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self.current_plan: Optional[Dict[str, Any]] = None
        self.current_step_index = 0
        
        # Recovery and meta-reasoning
        self.stuck_count = 0
        self.max_stuck_attempts = 3
        self.step_retry_count = 0
        self.max_step_retries = 3
        self.total_steps = 0
        self.max_total_steps = 200  # Prevent infinite loops
        self.last_element_count = 0  # NEW: Track element count for replan detection
        
        # Performance tracking
        self.start_time: Optional[float] = None
        self.metrics: Dict[str, Any] = {
            "steps_completed": 0,
            "retries": 0,
            "captchas_solved": 0,
            "tools_used": 0,
            "success_rate": 0.0,
            "replans": 0  # NEW: Track replanning events
        }
    
    async def emit(self, event_type: str, data: Dict[str, Any]):
        """Emit event to frontend via WebSocket"""
        if self.ws_callback:
            event = {
                "type": event_type,
                "data": data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent_state": self.state.value,
                "session_id": self.session_id,
                "task_id": self.task_id
            }
            try:
                await self.ws_callback(event)
            except Exception as e:
                logger.error(f"WebSocket emit failed: {e}")
    
    async def run(self, goal: str, context: Dict[str, Any] = None, user_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main execution entry point. Runs the full autonomous automation cycle.
        
        Args:
            goal: The task to accomplish (e.g., "Register on justfans.uno")
            context: Additional context like target_url, timeout, etc.
            user_data: User-provided data (email, password, etc.) or None for auto-generation
            
        Returns:
            Execution result with status, resources, and metrics
        """
        self.task_id = str(uuid.uuid4())
        self.current_goal = goal
        self.start_time = time.time()
        self.state = AgentState.ANALYZING
        
        logger.info(f"🚀 [AGENT] Starting task: {goal}")
        await self.emit("task_started", {
            "goal": goal,
            "context": context or {},
            "task_id": self.task_id
        })
        
        try:
            # Phase 1: Meta-Planning (High-level strategy)
            await self.emit("phase_started", {"phase": "meta_planning"})
            
            meta_plan = await self.meta_planner.create_plan(goal, context, user_data)
            if meta_plan.get("status") == "NEEDS_USER_DATA":
                self.state = AgentState.WAITING_USER
                return meta_plan
            
            self.current_plan = meta_plan
            await self.emit("plan_created", meta_plan)
            
            # Phase 2: Resource Initialization (Tools)
            await self.emit("phase_started", {"phase": "resource_init"})
            
            required_tools = meta_plan.get("required_tools", [])
            for tool_name in required_tools:
                result = await self.tools.execute(tool_name, {})
                self.resources.update(result)
                self.metrics["tools_used"] += 1
                
                await self.emit("tool_executed", {
                    "tool": tool_name,
                    "result": result
                })
            
            # Phase 3: Session Management  
            await self.emit("phase_started", {"phase": "session_setup"})
            
            self.session_id = await self._setup_session(meta_plan)
            
            # Phase 4: Main Execution Loop
            await self.emit("phase_started", {"phase": "execution"})
            self.state = AgentState.EXECUTING
            
            success = await self._execution_loop()
            
            if success:
                self.state = AgentState.COMPLETED
                result = {
                    "status": "SUCCESS",
                    "task_id": self.task_id,
                    "resources": self.resources,
                    "metrics": self._calculate_metrics(),
                    "execution_time": time.time() - self.start_time
                }
            else:
                self.state = AgentState.FAILED  
                result = {
                    "status": "FAILED",
                    "task_id": self.task_id, 
                    "reason": "Execution loop failed",
                    "metrics": self._calculate_metrics(),
                    "execution_time": time.time() - self.start_time
                }
            
            await self.emit("task_completed", result)
            return result
            
        except Exception as e:
            logger.error(f"❌ [AGENT] Fatal error: {e}")
            self.state = AgentState.FAILED
            
            result = {
                "status": "ERROR",
                "task_id": self.task_id,
                "error": str(e),
                "metrics": self._calculate_metrics(),
                "execution_time": time.time() - self.start_time if self.start_time else 0
            }
            await self.emit("task_failed", result)
            return result
    
    async def _setup_session(self, meta_plan: Dict[str, Any]) -> str:
        """Setup browser session with appropriate profile and proxy"""
        try:
            # Use existing profile or create new one
            needs_warm = meta_plan.get("requirements", {}).get("needs_warm_profile", False)
            profile_id = meta_plan.get("profile_id")
            
            if not profile_id:
                # Create new profile
                from routes.profile_routes import create_profile, CreateProfileRequest
                prof_resp = await create_profile(CreateProfileRequest(warmup=needs_warm, region="US"))
                profile_id = prof_resp.get('profile_id')
            
            # Create session from profile
            session_id = str(uuid.uuid4())
            await browser_service.create_session_from_profile(
                profile_id=profile_id,
                session_id=session_id
            )
            
            logger.info(f"✅ [AGENT] Session created: {session_id}")
            await self.emit("session_created", {
                "session_id": session_id,
                "profile_id": profile_id,
                "needs_warm": needs_warm
            })
            
            return session_id
            
        except Exception as e:
            logger.error(f"❌ [AGENT] Session setup failed: {e}")
            raise
    
    async def _execution_loop(self) -> bool:
        """
        Main execution loop with built-in recovery and meta-reasoning.
        Returns True if goal achieved, False if failed.
        """
        # Get plan steps
        steps = self.current_plan.get("steps", [])
        if not steps:
            logger.error("No steps in plan!")
            return False
        
        # Navigate to target URL first
        target_url = self.current_plan.get("target_url")
        if target_url:
            await self._navigate_initial(target_url)
        
        # Execute each step with recovery
        while self.current_step_index < len(steps) and self.total_steps < self.max_total_steps:
            self.total_steps += 1
            
            step = steps[self.current_step_index]
            logger.info(f"🔄 [AGENT] Step {self.current_step_index + 1}/{len(steps)}: {step.get('action', 'unknown')}")
            
            # Execute step
            success = await self._execute_step(step)
            
            if success:
                # Step succeeded, move to next
                self.current_step_index += 1
                self.step_retry_count = 0
                self.stuck_count = 0
                self.metrics["steps_completed"] += 1
                
                await self.emit("step_completed", {
                    "step_index": self.current_step_index,
                    "step": step,
                    "total_steps": len(steps)
                })
                
                # Check if goal achieved
                if await self._check_goal_completion():
                    logger.info("🎉 [AGENT] Goal achieved!")
                    return True
                    
            else:
                # Step failed, try recovery
                self.step_retry_count += 1
                self.metrics["retries"] += 1
                
                if self.step_retry_count >= self.max_step_retries:
                    # Too many retries, try meta-reasoning
                    recovery_success = await self._meta_reasoning_recovery(step)
                    
                    if not recovery_success:
                        logger.error("❌ [AGENT] Meta-reasoning recovery failed")
                        return False
                    
                    # Reset retry count after successful recovery
                    self.step_retry_count = 0
        
        # Check final status
        if self.total_steps >= self.max_total_steps:
            logger.error("❌ [AGENT] Max steps reached")
            return False
        
        # All steps completed
        return await self._check_goal_completion()
    
    async def _execute_step(self, step: Dict[str, Any]) -> bool:
        """
        Execute a single step with perception, decision, and action.
        Returns True if successful, False if needs retry.
        """
        try:
            # 1. Perceive current state
            perception = await self.perception.capture_state(self.session_id)
            
            # 1.5 NEW: Update workflow state based on perception
            new_workflow_state = await self.state_machine.determine_state(
                perception=perception,
                previous_state=self.state_machine.current_state,
                goal=self.current_goal
            )
            
            if new_workflow_state != self.state_machine.current_state:
                self.state_machine.transition_to(new_workflow_state, {
                    "step_index": self.current_step_index,
                    "step_action": step.get("action")
                })
                await self.emit("workflow_state_changed", {
                    "state": new_workflow_state.value,
                    "description": self.state_machine.get_state_description(new_workflow_state)
                })
            
            # 1.6 NEW: Check if replanning needed (before making decision)
            if await self._check_replan_trigger(perception, step):
                logger.info("🔄 [AGENT] Replan trigger detected")
                new_plan = await self._dynamic_replan(perception)
                if new_plan:
                    # Successfully replanned, restart from first step of new plan
                    return True
                else:
                    # Replanning failed, continue with current plan
                    logger.warning("⚠️ [AGENT] Replanning failed, continuing with current plan")
            
            # Add workflow state to perception for tactical brain
            perception['workflow_state'] = new_workflow_state.value
            self.previous_workflow_state = new_workflow_state
            
            # Track element count for replan detection
            self.last_element_count = len(perception.get('vision', []))
            
            # 2. Make tactical decision
            decision = await self.tactical.decide(
                step=step,
                perception=perception,
                resources=self.resources,
                history=self.execution_history[-5:]  # Last 5 steps for context
            )
            
            # 3. Handle tool calls first
            if decision.get("tool_call"):
                tool_result = await self.tools.execute(
                    decision["tool_call"]["name"],
                    decision["tool_call"]["params"]
                )
                self.resources.update(tool_result)
                self.metrics["tools_used"] += 1
                
                await self.emit("tool_executed", {
                    "tool": decision["tool_call"]["name"],
                    "result": tool_result
                })
                return True  # Tool execution counts as step success
            
            # 4. Execute browser action
            if decision.get("action"):
                action_result = await self.execution.execute(
                    action=decision["action"],
                    session_id=self.session_id,
                    resources=self.resources
                )
                
                # Log execution
                self.execution_history.append({
                    "step": step,
                    "decision": decision,
                    "result": action_result,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                await self.emit("action_executed", {
                    "action": decision["action"],
                    "result": action_result,
                    "step": step
                })
                
                # 5. Verify result
                if action_result.get("success"):
                    # Wait for page to settle
                    await asyncio.sleep(2)
                    
                    # Get new perception for validation
                    new_perception = await self.perception.capture_state(self.session_id)
                    
                    # Verify step completion
                    is_completed = await self.verification.verify_step(
                        step=step,
                        before_perception=perception,
                        after_perception=new_perception,
                        action_result=action_result
                    )
                    
                    return is_completed
                else:
                    logger.warning(f"⚠️ [AGENT] Action failed: {action_result.get('error')}")
                    return False
            
            logger.warning("⚠️ [AGENT] No action decided")
            return False
            
        except Exception as e:
            logger.error(f"❌ [AGENT] Step execution error: {e}")
            return False
    
    async def _navigate_initial(self, url: str):
        """Navigate to initial URL with error handling"""
        try:
            logger.info(f"🌐 [AGENT] Navigating to {url}")
            result = await browser_service.navigate(self.session_id, url)
            
            if not result.get("success"):
                raise Exception(f"Navigation failed: {result.get('error')}")
                
            await self.emit("navigation_completed", {
                "url": url,
                "result": result
            })
            
            # Wait for page to fully load
            await asyncio.sleep(3)
            
        except Exception as e:
            logger.error(f"❌ [AGENT] Navigation error: {e}")
            raise
    
    async def _check_goal_completion(self) -> bool:
        """Check if the main goal has been achieved"""
        try:
            perception = await self.perception.capture_state(self.session_id)
            
            # Use verification service to check goal completion
            is_complete = await self.verification.verify_goal(
                goal=self.current_goal,
                perception=perception,
                resources=self.resources,
                plan=self.current_plan
            )
            
            return is_complete
            
        except Exception as e:
            logger.error(f"❌ [AGENT] Goal completion check failed: {e}")
            return False
    
    async def _check_replan_trigger(self, perception: Dict[str, Any], step: Dict[str, Any]) -> bool:
        """
        NEW: Determine if replanning is needed based on current state
        
        Triggers:
        1. Expected elements not found
        2. Page structure significantly different
        3. Unexpected workflow state
        4. Repeated failures on same step type
        """
        try:
            # Trigger 1: Expected elements not found
            expected_elements = step.get('pre', {}).get('elements', [])
            if expected_elements:
                available = [e.get('label', '').lower() for e in perception.get('vision', [])]
                missing = [exp for exp in expected_elements if not any(exp.lower() in av for av in available)]
                if len(missing) > len(expected_elements) / 2:  # More than half missing
                    logger.info(f"🔄 [AGENT] Replan trigger: Expected elements missing ({len(missing)}/{len(expected_elements)})")
                    return True
            
            # Trigger 2: Page structure significantly different
            if self.last_element_count > 0:
                current_count = len(perception.get('vision', []))
                element_diff = abs(current_count - self.last_element_count)
                if element_diff > 15:  # Significant change
                    logger.info(f"🔄 [AGENT] Replan trigger: Page structure changed significantly (Δ{element_diff} elements)")
                    return True
            
            # Trigger 3: Unexpected workflow state
            current_state = self.state_machine.current_state
            expected_states = self.state_machine.get_valid_transitions(self.previous_workflow_state)
            expected_states.append(self.previous_workflow_state)  # Can stay in same state
            
            if current_state not in expected_states and current_state not in [WorkflowState.ERROR_STATE, WorkflowState.INITIAL]:
                logger.info(f"🔄 [AGENT] Replan trigger: Unexpected workflow state ({current_state.value})")
                return True
            
            # Trigger 4: Repeated failures on same step type
            if self.step_retry_count >= 2:
                logger.info(f"🔄 [AGENT] Replan trigger: Repeated failures (retry {self.step_retry_count})")
                return True
            
            # Trigger 5: Stuck in CAPTCHA or verification
            if current_state in [WorkflowState.HANDLING_CAPTCHA, WorkflowState.EMAIL_VERIFICATION]:
                # Check how long we've been in this state
                state_history = self.state_machine.get_state_history_summary()
                same_state_count = sum(1 for h in state_history[-5:] if h.get('to') == current_state.value)
                if same_state_count >= 3:
                    logger.info(f"🔄 [AGENT] Replan trigger: Stuck in {current_state.value}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ [AGENT] Replan trigger check failed: {e}")
            return False
    
    async def _dynamic_replan(self, perception: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        NEW: Generate new plan from current state when original plan becomes invalid
        
        Returns:
            New plan dict if successful, None if replanning failed
        """
        logger.info("🔄 [AGENT] Starting dynamic replanning")
        self.metrics["replans"] += 1
        
        try:
            # Format execution history for context
            history_summary = []
            for h in self.execution_history[-5:]:
                history_summary.append({
                    "step": h.get("step", {}).get("action"),
                    "success": h.get("result", {}).get("success", False),
                    "timestamp": h.get("timestamp")
                })
            
            # Format elements for LLM
            elements_summary = []
            for elem in perception.get('vision', [])[:25]:  # Top 25 elements
                elements_summary.append(
                    f"  - Cell {elem.get('cell', '?')}: {elem.get('type', 'unknown')} "
                    f"'{elem.get('label', 'no label')}'"
                )
            
            replan_prompt = f"""
# DYNAMIC REPLANNING REQUEST

## SITUATION
The original automation plan is no longer valid. We need a NEW plan from the current state to reach the goal.

**Original Goal:** {self.current_goal}

**Original Plan Progress:** 
- Completed {self.current_step_index}/{len(self.current_plan.get('steps', []))} steps
- Current step was: {self.current_plan.get('steps', [{}])[self.current_step_index] if self.current_step_index < len(self.current_plan.get('steps', [])) else 'N/A'}

**Current Page State:**
- URL: {perception.get('url')}
- Page Type: {perception.get('page_analysis', {}).get('page_type')}
- Workflow State: {self.state_machine.current_state.value}

**Available Elements on Page:**
{chr(10).join(elements_summary)}

**Page Analysis:**
- Forms: {len(perception.get('page_analysis', {}).get('forms', []))}
- Buttons: {len([e for e in perception.get('vision', []) if e.get('type') == 'button'])}
- Text Inputs: {len([e for e in perception.get('vision', []) if e.get('type') in ['textbox', 'input']])}
- Errors: {perception.get('page_analysis', {}).get('errors', [])}
- Success Messages: {perception.get('page_analysis', {}).get('success_messages', [])}

**What We've Already Tried:**
{chr(10).join([f"  - {h['step']} ({'✓' if h['success'] else '✗'})" for h in history_summary])}

**Available Resources:**
{list(self.resources.keys())}

## REPLANNING TASK

Create a NEW step-by-step plan that:
1. Starts from CURRENT page state (not from beginning)
2. Works with ACTUAL elements present on the page (use real cell IDs)
3. Accounts for what we've already tried (don't repeat failures)
4. Adapts to current workflow state
5. Has concrete, achievable steps with specific cell targets

Return JSON:
{{
    "situation_analysis": "Brief analysis of why replanning was needed",
    "current_state_assessment": "Where we are now in the workflow",
    "goal_still_achievable": true/false,
    "adjusted_goal": "Same goal or adjusted if needed",
    
    "new_plan": {{
        "strategy": "Brief description of new approach",
        "steps": [
            {{
                "id": "replan_step_1",
                "action": "TYPE|CLICK|WAIT|SUBMIT_FORM|...",
                "target": {{"by": "label", "value": "exact element label from list above"}},
                "field": "field_name",
                "data_key": "resource_key",
                "description": "Human-readable description",
                "expected_outcome": "What should happen after this step",
                "retry_strategy": "What to do if this step fails"
            }}
            // Add 3-8 concrete steps
        ]
    }},
    
    "confidence": 0.0-1.0,
    "risk_factors": ["potential issues with new plan"]
}}

IMPORTANT: Use ONLY elements that are actually visible in the "Available Elements" list above.
"""
            
            # Call head brain for replanning
            response = await head_brain_service._call_openrouter(
                system_prompt="You are an expert automation replanner. Create adaptive, concrete plans based on current page state. Always use actual visible elements.",
                user_prompt=replan_prompt
            )
            
            if not response or response.get('error'):
                logger.error(f"❌ [AGENT] Replanning LLM call failed: {response.get('error') if response else 'No response'}")
                return None
            
            # Extract new plan
            if isinstance(response, dict) and 'new_plan' in response:
                new_plan_data = response['new_plan']
            elif isinstance(response, dict) and 'steps' in response:
                # Sometimes LLM returns the plan directly
                new_plan_data = response
            else:
                logger.error("❌ [AGENT] Invalid replan response format")
                return None
            
            # Validate new plan has steps
            if not new_plan_data.get('steps') or len(new_plan_data.get('steps', [])) < 1:
                logger.error("❌ [AGENT] New plan has no steps")
                return None
            
            # Update current plan
            self.current_plan['steps'] = new_plan_data['steps']
            self.current_plan['strategy'] = new_plan_data.get('strategy', 'Replanned from current state')
            self.current_step_index = 0  # Start new plan from beginning
            self.step_retry_count = 0  # Reset retry counter
            
            await self.emit("plan_updated", {
                "reason": response.get('situation_analysis', 'Dynamic replanning'),
                "new_strategy": new_plan_data.get('strategy'),
                "new_steps_count": len(new_plan_data['steps']),
                "confidence": response.get('confidence', 0.5)
            })
            
            logger.info(f"✅ [AGENT] New plan created: {len(new_plan_data['steps'])} steps")
            return new_plan_data
            
        except Exception as e:
            logger.error(f"❌ [AGENT] Dynamic replanning failed: {e}")
            return None
    
    async def _meta_reasoning_recovery(self, failed_step: Dict[str, Any]) -> bool:
        """
        Meta-reasoning when stuck. Analyzes situation and attempts recovery.
        Returns True if recovery successful, False if should abort.
        """
        self.state = AgentState.META_REASONING
        self.stuck_count += 1
        
        logger.info(f"🧠 [AGENT] Meta-reasoning attempt {self.stuck_count}/{self.max_stuck_attempts}")
        
        try:
            # Get current perception for analysis
            perception = await self.perception.capture_state(self.session_id)
            
            # NEW: Enhanced meta-reasoning prompt with structured analysis framework
            # Get before/after perception for better analysis
            before_perception = self.execution_history[-1].get("perception_before", {}) if self.execution_history else {}
            after_perception = perception
            
            analysis_prompt = f"""
# META-REASONING ANALYSIS - IMPROVED WITH STRUCTURED FRAMEWORK

## CURRENT SITUATION
**Original Goal:** {self.current_goal}
**Current Plan:** Step {self.current_step_index + 1}/{len(self.current_plan.get('steps', []))} - {self.current_plan.get('strategy', 'N/A')}
**Workflow State:** {self.state_machine.current_state.value} ({self.state_machine.get_state_description()})

**Failed Step Details:**
- Action: {failed_step.get('action')}
- Target: {failed_step.get('target')}
- Field: {failed_step.get('field', 'N/A')}
- Expected Outcome: {failed_step.get('expected_outcome', 'N/A')}
- Failure Count: {self.step_retry_count}/3

## PAGE STATE ANALYSIS
**Current Page:**
- URL: {after_perception.get('url')}
- Page Type: {after_perception.get('page_analysis', {}).get('page_type')}
- Visible Elements: {len(after_perception.get('vision', []))} interactive elements
- Forms: {len(after_perception.get('page_analysis', {}).get('forms', []))}
- Buttons: {len([e for e in after_perception.get('vision', []) if e.get('type') == 'button'])}
- Text Inputs: {len([e for e in after_perception.get('vision', []) if e.get('type') in ['textbox', 'input']])}

**Errors Present:** {after_perception.get('page_analysis', {}).get('errors', [])}
**Success Messages:** {after_perception.get('page_analysis', {}).get('success_messages', [])}

**Element Sample (top 10):**
{chr(10).join([f"  - {e.get('cell', '?')}: {e.get('type', '?')} '{e.get('label', 'no label')}'" for e in after_perception.get('vision', [])[:10]])}

## EXECUTION HISTORY (Last 5 Steps)
{chr(10).join([f"  {i+1}. {h.get('step', {}).get('action', '?')} - {'✓ Success' if h.get('result', {}).get('success') else '✗ Failed'}" for i, h in enumerate(self.execution_history[-5:])])}

## RESOURCES AVAILABLE
{', '.join(self.resources.keys()) if self.resources else 'None'}

## REASONING FRAMEWORK

Please analyze using this structured approach:

### 1. Root Cause Analysis
**What specifically failed?**
- Element not found?
- Action rejected by page?
- Unexpected page state?
- Validation error?

**Why did it fail?**
- Wrong selector/element?
- Page changed structure?
- Timing issue (too fast/slow)?
- Data validation failed?
- Anti-bot detection?

### 2. Current State Assessment
**Are we still on the right path towards the goal?**
- Has the workflow deviated from expected flow?
- Are we on an unexpected page?
- Are there signs we're closer or further from goal?

### 3. Alternative Path Analysis
**Can we achieve the same sub-goal differently?**
- Are there alternative elements to interact with?
- Should we adjust our approach based on page changes?
- Is there a different route to the same outcome?

### 4. Goal Proximity Check
**Despite the failure, are we actually closer to goal completion?**
- Has the goal been partially achieved already?
- Are we on a success page despite step failure?
- Do we need to continue or reassess?

### 5. Recovery Strategy Selection

**Select BEST strategy from these options:**

**A. REPLAN** - Generate new step sequence from current state
- Use when: Page structure differs significantly from expectations
- Action: Analyze current page and create new tactical plan

**B. ALTERNATIVE_ELEMENT** - Try different element for same action  
- Use when: Target element not found but alternatives exist
- Action: Identify and use alternative element with better confidence

**C. NEW_RESOURCES** - Generate fresh credentials/data
- Use when: Current data rejected (email taken, username exists, etc.)
- Action: Generate new email/password/username and retry

**D. NAVIGATE_BACK** - Return to known good state
- Use when: In wrong location or stuck in error loop
- Action: Navigate to specific URL to reset

**E. SKIP_AND_CONTINUE** - Bypass problematic step
- Use when: Step is optional or goal achievable without it
- Action: Move to next step in plan

**F. WAIT_AND_OBSERVE** - Pause for page to load/settle
- Use when: Timing issue or async loading suspected
- Action: Wait longer (5-10s) and re-assess

**G. HUMAN_INTERVENTION** - Cannot proceed autonomously
- Use when: CAPTCHA unsolvable, phone verification required, fundamental blocker
- Action: Request human assistance with specific instructions

## REQUIRED JSON RESPONSE

{{
    "root_cause": "Detailed explanation of WHY we failed (be specific)",
    "current_state_assessment": "Are we on track? Closer or further from goal?",
    "goal_proximity": 0.0-1.0,  // How close to completing goal (0=not started, 1=achieved)
    "blocking_factor": "What's preventing progress?",
    
    "recovery_strategy": "REPLAN|ALTERNATIVE_ELEMENT|NEW_RESOURCES|NAVIGATE_BACK|SKIP_AND_CONTINUE|WAIT_AND_OBSERVE|HUMAN_INTERVENTION",
    
    "recovery_action": {{
        "type": "specific action type",
        "params": {{}},
        "reasoning": "Why this specific action will work"
    }},
    
    "alternative_elements": [
        {{"cell": "B5", "label": "Sign Up", "reason": "Alternative button with higher visibility"}}
    ],
    
    "should_replan": true/false,
    "new_plan_outline": "If replanning recommended, brief outline of new approach",
    
    "confidence": 0.0-1.0,
    "require_human": true/false,
    "human_instructions": "If human needed, EXACTLY what should they do"
}}

**IMPORTANT:** Be specific and actionable. Don't just say "element not found" - explain WHICH element, WHY it's not found, and WHAT alternatives exist.
"""
            
            # Use head brain for meta-reasoning
            analysis = await head_brain_service._call_openrouter(
                system_prompt="You are an expert automation troubleshooter. Analyze stuck situations and propose recovery strategies.",
                user_prompt=analysis_prompt
            )
            
            if not analysis or analysis.get("error"):
                logger.error("Meta-reasoning analysis failed")
                return False
            
            await self.emit("meta_reasoning", {
                "diagnosis": analysis.get("diagnosis"),
                "strategy": analysis.get("recovery_strategy"),
                "confidence": analysis.get("confidence")
            })
            
            # Execute recovery strategy
            recovery_strategy = analysis.get("recovery_strategy", "give_up")
            
            if recovery_strategy == "new_resources":
                # Generate new resources
                if "email" in analysis.get("recovery_action", {}).get("params", {}):
                    email_result = await self.tools.execute("create_temp_email", {})
                    self.resources.update(email_result)
                
                if "password" in analysis.get("recovery_action", {}).get("params", {}):
                    password_result = await self.tools.execute("generate_password", {})
                    self.resources.update(password_result)
                
                return True  # Try again with new resources
                
            elif recovery_strategy == "navigate":
                # Navigate to different page
                new_url = analysis.get("recovery_action", {}).get("params", {}).get("url")
                if new_url:
                    await self._navigate_initial(new_url)
                    return True
                    
            elif recovery_strategy == "skip":
                # Skip current step
                self.current_step_index += 1
                return True
                
            elif recovery_strategy == "retry":
                # Just retry (reset retry count)
                return True
                
            else:  # give_up or unknown
                if self.stuck_count >= self.max_stuck_attempts:
                    self.state = AgentState.WAITING_USER
                    await self.emit("human_intervention_required", {
                        "reason": analysis.get("diagnosis", "Automation stuck"),
                        "step": failed_step,
                        "resources": self.resources
                    })
                    return False
                else:
                    return True  # Try once more
            
        except Exception as e:
            logger.error(f"❌ [AGENT] Meta-reasoning failed: {e}")
            
            if self.stuck_count >= self.max_stuck_attempts:
                return False
            else:
                return True  # Try basic retry
    
    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics"""
        total_time = (time.time() - self.start_time) if self.start_time else 0
        
        self.metrics.update({
            "total_steps": self.total_steps,
            "success_rate": (self.metrics["steps_completed"] / max(1, self.total_steps)) * 100,
            "execution_time": total_time,
            "steps_per_minute": (self.total_steps / max(1, total_time / 60)) if total_time > 0 else 0,
            "retry_rate": (self.metrics["retries"] / max(1, self.total_steps)) * 100
        })
        
        return self.metrics
    
    async def pause(self):
        """Pause execution"""
        self.state = AgentState.IDLE
        await self.emit("agent_paused", {})
    
    async def resume(self):
        """Resume execution"""  
        self.state = AgentState.EXECUTING
        await self.emit("agent_resumed", {})
    
    async def stop(self):
        """Stop execution and cleanup"""
        self.state = AgentState.IDLE
        
        if self.session_id:
            try:
                await browser_service.close_session(self.session_id)
            except Exception as e:
                logger.warning(f"Session cleanup failed: {e}")
        
        await self.emit("agent_stopped", {
            "final_metrics": self._calculate_metrics()
        })


# Global instance for integration with existing hook_routes.py
autonomous_agent = AutonomousAgent()