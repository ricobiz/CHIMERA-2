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
        
        # State
        self.state = AgentState.IDLE
        self.session_id: Optional[str] = None
        self.task_id: Optional[str] = None
        self.current_goal: str = ""
        
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
        
        # Performance tracking
        self.start_time: Optional[float] = None
        self.metrics: Dict[str, Any] = {
            "steps_completed": 0,
            "retries": 0,
            "captchas_solved": 0,
            "tools_used": 0,
            "success_rate": 0.0
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
            
            # Analyze why we're stuck using head brain service
            analysis_prompt = f"""
            Task: {self.current_goal}
            
            Failed step: {failed_step}
            
            Current state: {perception.get('summary', 'Unknown')}
            
            Resources available: {self.resources}
            
            Execution history: {self.execution_history[-3:]}
            
            Why are we stuck? How can we recover?
            
            Options:
            1. Retry with different approach
            2. Generate new resources (email, password, etc.)  
            3. Navigate to different page
            4. Skip this step and continue
            5. Give up and require human intervention
            
            Return JSON:
            {{
                "diagnosis": "reason we're stuck",
                "recovery_strategy": "retry|new_resources|navigate|skip|give_up",
                "recovery_action": {{"action": "...", "params": {{...}}}},
                "confidence": 0.0-1.0,
                "require_human": true/false
            }}
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