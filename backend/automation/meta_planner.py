"""
Meta Planner - High-level strategic planning
Integrates with existing head_brain_service and planner_service
"""

import logging
from typing import Dict, Any, Optional

from services.head_brain_service import head_brain_service
from services.planner_service import planner_service

logger = logging.getLogger(__name__)

class MetaPlanner:
    """
    Meta-level planner that creates high-level strategies and delegates 
    to existing head_brain_service and planner_service
    """
    
    def __init__(self):
        self.head_brain = head_brain_service
        self.planner = planner_service
    
    async def create_plan(
        self, 
        goal: str, 
        context: Optional[Dict[str, Any]] = None,
        user_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create comprehensive plan using existing services
        
        Returns:
            - Full plan with strategy, steps, resources, and tools needed
            - Or NEEDS_USER_DATA status if data required
        """
        try:
            logger.info(f"🧠 [META-PLANNER] Creating plan for: {goal}")
            
            # Use existing head brain service for analysis
            profile_info = None  # Will be enhanced with profile detection
            auto_generate = user_data is None
            
            head_analysis = await self.head_brain.analyze_and_plan(
                goal=goal,
                profile_info=profile_info,
                user_data=user_data,
                auto_generate=auto_generate
            )
            
            # Handle user data requirements
            if head_analysis.get("status") == "NEEDS_USER_DATA":
                return head_analysis
            
            # Extract key information from head brain
            target_url = head_analysis.get("target_url")
            strategy = head_analysis.get("strategy")
            data_bundle = head_analysis.get("data_bundle", {})
            
            # Determine required tools based on task
            required_tools = self._determine_required_tools(goal, head_analysis)
            
            # Create detailed execution steps
            steps = self._create_execution_steps(head_analysis)
            
            # Build comprehensive plan
            plan = {
                "task_id": head_analysis.get("task_id"),
                "goal": goal,
                "target_url": target_url,
                "strategy": strategy,
                "understanding": head_analysis.get("understood_task", goal),
                "requirements": head_analysis.get("requirements", {}),
                "success_probability": head_analysis.get("success_probability", 0.7),
                
                # Resources and tools
                "data_bundle": data_bundle,
                "data_source": head_analysis.get("data_source", "generated"),
                "required_tools": required_tools,
                
                # Execution plan  
                "steps": steps,
                "max_steps": len(steps) * 2,  # Allow retries
                "timeout_minutes": 15,
                
                # Recovery settings
                "retry_policy": {
                    "max_step_retries": 3,
                    "max_meta_reasoning_attempts": 3,
                    "backoff_strategy": "exponential"
                },
                
                # Success criteria
                "success_indicators": self._define_success_indicators(goal, target_url),
                
                # Meta information
                "profile_info": head_analysis.get("profile_status", {}),
                "can_proceed": head_analysis.get("can_proceed", True),
                "reason": head_analysis.get("reason", "Analysis complete")
            }
            
            logger.info(f"✅ [META-PLANNER] Plan created: {len(steps)} steps, {len(required_tools)} tools")
            return plan
            
        except Exception as e:
            logger.error(f"❌ [META-PLANNER] Planning failed: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "can_proceed": False
            }
    
    def _determine_required_tools(self, goal: str, analysis: Dict[str, Any]) -> List[str]:
        """Determine what tools are needed for this task"""
        tools = []
        goal_lower = goal.lower()
        
        # Email tool for registrations
        if any(keyword in goal_lower for keyword in ["register", "signup", "create account", "регистр"]):
            tools.append("create_temp_email")
        
        # Password generator
        if "password" in analysis.get("requirements", {}).get("mandatory_data", []):
            tools.append("generate_password")
        
        # Phone number for verification
        if analysis.get("requirements", {}).get("needs_phone"):
            tools.append("get_phone_number")
        
        # Proxy for anti-detection
        if analysis.get("requirements", {}).get("needs_warm_profile"):
            tools.append("setup_proxy")
        
        # CAPTCHA solver (always available)
        tools.append("solve_captcha")
        
        # Data generator for missing fields
        if analysis.get("data_source") == "generated":
            tools.append("generate_user_data")
        
        return tools
    
    def _create_execution_steps(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create detailed execution steps from head brain analysis.
        If head brain provided steps, use those. Otherwise create generic steps.
        """
        # Check if head brain already provided detailed steps
        existing_steps = analysis.get("steps", [])
        if existing_steps and len(existing_steps) > 2:
            # Head brain provided good steps, use them
            return self._enhance_steps(existing_steps, analysis)
        
        # Create generic steps based on task type
        task_type = analysis.get("task_type", "navigation")
        target_url = analysis.get("target_url", "")
        
        if task_type == "registration":
            return self._create_registration_steps(target_url, analysis)
        elif task_type == "login":
            return self._create_login_steps(target_url, analysis)
        elif task_type == "form_fill":
            return self._create_form_fill_steps(target_url, analysis)
        else:
            return self._create_navigation_steps(target_url, analysis)
    
    def _create_registration_steps(self, target_url: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create steps for registration flow"""
        data_bundle = analysis.get("data_bundle", {})
        
        steps = [
            {
                "id": "step_1",
                "action": "NAVIGATE",
                "target": target_url,
                "description": "Navigate to registration page",
                "expected_outcome": "Registration form visible",
                "retry_strategy": "reload_page"
            },
            {
                "id": "step_2", 
                "action": "TYPE",
                "field": "first_name",
                "data_key": "first_name",
                "target": {"by": "label", "value": "first name"},
                "description": f"Enter first name: {data_bundle.get('first_name', 'auto')}",
                "expected_outcome": "First name field filled",
                "retry_strategy": "clear_and_retype"
            },
            {
                "id": "step_3",
                "action": "TYPE", 
                "field": "last_name",
                "data_key": "last_name",
                "target": {"by": "label", "value": "last name"},
                "description": f"Enter last name: {data_bundle.get('last_name', 'auto')}",
                "expected_outcome": "Last name field filled",
                "retry_strategy": "clear_and_retype"
            },
            {
                "id": "step_4",
                "action": "TYPE",
                "field": "email",
                "data_key": "email", 
                "target": {"by": "label", "value": "email"},
                "description": f"Enter email: {data_bundle.get('email', 'auto')}",
                "expected_outcome": "Email field filled",
                "retry_strategy": "generate_new_email"
            },
            {
                "id": "step_5",
                "action": "TYPE",
                "field": "password",
                "data_key": "password",
                "target": {"by": "label", "value": "password"},
                "description": "Enter password",
                "expected_outcome": "Password field filled", 
                "retry_strategy": "generate_new_password"
            },
            {
                "id": "step_6",
                "action": "TYPE",
                "field": "confirm_password", 
                "data_key": "password",
                "target": {"by": "label", "value": "confirm"},
                "description": "Confirm password",
                "expected_outcome": "Password confirmation filled",
                "retry_strategy": "clear_and_retype"
            },
            {
                "id": "step_7",
                "action": "CLICK",
                "target": {"by": "label", "value": "register"},
                "description": "Click registration button",
                "expected_outcome": "Form submitted or verification page shown",
                "retry_strategy": "find_alternative_submit"
            },
            {
                "id": "step_8",
                "action": "VERIFY_RESULT",
                "description": "Verify registration success or handle verification",
                "expected_outcome": "Registration completed or phone verification required",
                "retry_strategy": "wait_for_user_if_phone_needed"
            }
        ]
        
        return steps
    
    def _create_login_steps(self, target_url: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create steps for login flow"""
        return [
            {
                "id": "step_1",
                "action": "NAVIGATE",
                "target": target_url,
                "description": "Navigate to login page"
            },
            {
                "id": "step_2",
                "action": "TYPE",
                "field": "email",
                "data_key": "email",
                "target": {"by": "label", "value": "email"},
                "description": "Enter email"
            },
            {
                "id": "step_3", 
                "action": "TYPE",
                "field": "password",
                "data_key": "password",
                "target": {"by": "label", "value": "password"},
                "description": "Enter password"
            },
            {
                "id": "step_4",
                "action": "CLICK",
                "target": {"by": "label", "value": "login"},
                "description": "Click login button"
            },
            {
                "id": "step_5",
                "action": "VERIFY_RESULT", 
                "description": "Verify login success"
            }
        ]
    
    def _create_form_fill_steps(self, target_url: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create steps for generic form filling"""
        return [
            {
                "id": "step_1",
                "action": "NAVIGATE",
                "target": target_url,
                "description": "Navigate to form page"
            },
            {
                "id": "step_2",
                "action": "ANALYZE_FORM",
                "description": "Analyze form fields and requirements" 
            },
            {
                "id": "step_3",
                "action": "FILL_FORM",
                "description": "Fill all detected form fields"
            },
            {
                "id": "step_4",
                "action": "SUBMIT_FORM", 
                "description": "Submit the form"
            },
            {
                "id": "step_5",
                "action": "VERIFY_RESULT",
                "description": "Verify form submission success"
            }
        ]
    
    def _create_navigation_steps(self, target_url: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create steps for simple navigation"""
        return [
            {
                "id": "step_1", 
                "action": "NAVIGATE",
                "target": target_url,
                "description": "Navigate to target page"
            },
            {
                "id": "step_2",
                "action": "VERIFY_RESULT",
                "description": "Verify page loaded successfully"
            }
        ]
    
    def _enhance_steps(self, steps: List[Dict[str, Any]], analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Enhance existing steps with additional metadata"""
        enhanced_steps = []
        
        for i, step in enumerate(steps):
            enhanced_step = step.copy()
            
            # Add retry strategies
            if not enhanced_step.get("retry_strategy"):
                action = enhanced_step.get("action", "").upper()
                if action == "TYPE":
                    enhanced_step["retry_strategy"] = "clear_and_retype"
                elif action == "CLICK":
                    enhanced_step["retry_strategy"] = "find_alternative_element"
                elif action == "NAVIGATE":
                    enhanced_step["retry_strategy"] = "reload_page"
                else:
                    enhanced_step["retry_strategy"] = "wait_and_retry"
            
            # Add expected outcomes if missing
            if not enhanced_step.get("expected_outcome"):
                action = enhanced_step.get("action", "").upper()
                if action == "TYPE":
                    enhanced_step["expected_outcome"] = f"Field {enhanced_step.get('field', 'unknown')} filled"
                elif action == "CLICK":
                    enhanced_step["expected_outcome"] = "Element clicked successfully"
                elif action == "NAVIGATE":
                    enhanced_step["expected_outcome"] = "Page loaded successfully"
            
            # Add descriptions if missing
            if not enhanced_step.get("description"):
                enhanced_step["description"] = f"Execute {enhanced_step.get('action', 'unknown')} action"
            
            enhanced_steps.append(enhanced_step)
        
        return enhanced_steps
    
    def _define_success_indicators(self, goal: str, target_url: str) -> Dict[str, Any]:
        """Define what indicates successful completion"""
        indicators = {
            "url_patterns": [],
            "text_indicators": [],
            "element_indicators": [],
            "negative_indicators": []  # Things that indicate failure
        }
        
        goal_lower = goal.lower()
        
        if "register" in goal_lower or "signup" in goal_lower:
            indicators["url_patterns"] = [
                "/welcome", "/verify", "/dashboard", "/profile", "/home"
            ]
            indicators["text_indicators"] = [
                "welcome", "registration successful", "account created", "verify your email"
            ]
            indicators["element_indicators"] = [
                {"type": "text", "content": "logout"},
                {"type": "button", "content": "dashboard"}
            ]
            indicators["negative_indicators"] = [
                "error", "invalid", "already exists", "registration failed"
            ]
        
        elif "login" in goal_lower:
            indicators["url_patterns"] = ["/dashboard", "/home", "/profile", "/app"]
            indicators["text_indicators"] = ["welcome back", "dashboard", "logout"]
            indicators["negative_indicators"] = ["invalid credentials", "login failed", "wrong password"]
        
        return indicators


# Global instance
meta_planner = MetaPlanner()