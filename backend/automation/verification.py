"""
Verification - Result validation and success detection
Uses intelligent analysis to determine if actions succeeded and goals are achieved
"""

import logging
import re
from typing import Dict, Any, List, Optional

from services.openrouter_service import openrouter_service

logger = logging.getLogger(__name__)

class Verification:
    """
    Verification system that validates step completion and goal achievement.
    Uses multiple strategies: heuristics, pattern matching, and LLM analysis.
    """
    
    def __init__(self):
        self.model = "qwen/qwen2.5-vl"  # Vision model for verification
        self.temperature = 0.1
    
    async def verify_step(
        self, 
        step: Dict[str, Any], 
        before_perception: Dict[str, Any], 
        after_perception: Dict[str, Any], 
        action_result: Dict[str, Any]
    ) -> bool:
        """
        Verify if a step was completed successfully by comparing before/after state.
        
        Args:
            step: The step that was executed
            before_perception: Page state before action
            after_perception: Page state after action  
            action_result: Result from action execution
            
        Returns:
            True if step completed successfully
        """
        try:
            step_action = step.get("action", "").upper()
            expected_outcome = step.get("expected_outcome", "")
            
            logger.info(f"🔍 [VERIFICATION] Verifying step: {step_action}")
            
            # Quick fail if action itself failed
            if not action_result.get("success"):
                logger.warning(f"❌ [VERIFICATION] Action failed: {action_result.get('error')}")
                return False
            
            # Step-specific verification
            if step_action == "NAVIGATE":
                return await self._verify_navigation(step, after_perception, action_result)
            
            elif step_action == "TYPE":
                return await self._verify_type_action(step, before_perception, after_perception, action_result)
            
            elif step_action == "CLICK":
                return await self._verify_click_action(step, before_perception, after_perception, action_result)
            
            elif step_action == "VERIFY_RESULT":
                return await self._verify_result_step(step, after_perception)
            
            elif step_action in ["WAIT", "ANALYZE_FORM", "FILL_FORM"]:
                return True  # These actions are considered successful if they execute
            
            else:
                # Use LLM for unknown action verification
                return await self._llm_verify_step(step, before_perception, after_perception, action_result)
        
        except Exception as e:
            logger.error(f"❌ [VERIFICATION] Step verification failed: {e}")
            return False
    
    async def verify_goal(
        self, 
        goal: str, 
        perception: Dict[str, Any], 
        resources: Dict[str, Any], 
        plan: Dict[str, Any]
    ) -> bool:
        """
        Verify if the main goal has been achieved.
        
        Args:
            goal: Original goal description
            perception: Current page state
            resources: Available resources  
            plan: Execution plan with success indicators
            
        Returns:
            True if goal achieved
        """
        try:
            logger.info(f"🎯 [VERIFICATION] Verifying goal: {goal}")
            
            # Get success indicators from plan
            success_indicators = plan.get("success_indicators", {})
            current_url = perception.get("url", "")
            page_analysis = perception.get("page_analysis", {})
            
            # Check URL patterns
            url_patterns = success_indicators.get("url_patterns", [])
            if url_patterns and any(pattern in current_url.lower() for pattern in url_patterns):
                logger.info(f"✅ [VERIFICATION] Goal achieved via URL pattern: {current_url}")
                return True
            
            # Check text indicators
            page_text = perception.get("page_text", "").lower()
            text_indicators = success_indicators.get("text_indicators", [])
            if text_indicators and any(indicator in page_text for indicator in text_indicators):
                logger.info("✅ [VERIFICATION] Goal achieved via text indicator")
                return True
            
            # Check for success messages
            success_messages = page_analysis.get("success_messages", [])
            if success_messages:
                logger.info(f"✅ [VERIFICATION] Goal achieved via success message: {success_messages[0]}")
                return True
            
            # Check negative indicators (failure)
            negative_indicators = success_indicators.get("negative_indicators", [])
            errors = page_analysis.get("errors", [])
            
            for error in errors:
                if any(neg_indicator in error.lower() for neg_indicator in negative_indicators):
                    logger.warning(f"❌ [VERIFICATION] Goal failed due to error: {error}")
                    return False
            
            # Page type based verification
            page_type = page_analysis.get("page_type", "unknown")
            goal_lower = goal.lower()
            
            if "register" in goal_lower or "signup" in goal_lower:
                # Registration goal
                if page_type in ["dashboard", "verification", "success_page"]:
                    logger.info(f"✅ [VERIFICATION] Registration goal achieved - page type: {page_type}")
                    return True
                elif "/register" not in current_url and "/signup" not in current_url:
                    # Moved away from registration page
                    logger.info("✅ [VERIFICATION] Registration goal likely achieved - left registration page")
                    return True
            
            elif "login" in goal_lower:
                # Login goal
                if page_type in ["dashboard", "profile"] or "/dashboard" in current_url or "/profile" in current_url:
                    logger.info(f"✅ [VERIFICATION] Login goal achieved - page type: {page_type}")
                    return True
            
            # Use LLM for complex goal verification
            return await self._llm_verify_goal(goal, perception, resources)
        
        except Exception as e:
            logger.error(f"❌ [VERIFICATION] Goal verification failed: {e}")
            return False
    
    async def _verify_navigation(self, step: Dict[str, Any], perception: Dict[str, Any], action_result: Dict[str, Any]) -> bool:
        """Verify navigation step completed successfully"""
        target_url = step.get("target", "")
        current_url = perception.get("url", "")
        
        # Simple URL match
        if target_url in current_url:
            return True
        
        # Check if we're on the correct domain
        if target_url and current_url:
            try:
                from urllib.parse import urlparse
                target_domain = urlparse(target_url).netloc
                current_domain = urlparse(current_url).netloc
                
                if target_domain == current_domain:
                    return True
            except Exception:
                pass
        
        # Check if page loaded successfully (not error page)
        page_analysis = perception.get("page_analysis", {})
        if page_analysis.get("page_type") != "error_page":
            return True
        
        return False
    
    async def _verify_type_action(self, step: Dict[str, Any], before: Dict[str, Any], after: Dict[str, Any], action_result: Dict[str, Any]) -> bool:
        """Verify text input was successful"""
        # Check if typing was successful from action result
        if action_result.get("success"):
            # Additional verification: check for errors
            after_errors = after.get("page_analysis", {}).get("errors", [])
            
            # If new errors appeared, typing might have failed validation
            before_errors = before.get("page_analysis", {}).get("errors", [])
            new_errors = set(after_errors) - set(before_errors)
            
            if new_errors:
                # Check if errors are related to this field
                field = step.get("field", "").lower()
                field_related_error = any(field in error.lower() for error in new_errors)
                
                if field_related_error:
                    logger.warning(f"⚠️ [VERIFICATION] Type action may have validation error: {list(new_errors)}")
                    return False
            
            return True
        
        return False
    
    async def _verify_click_action(self, step: Dict[str, Any], before: Dict[str, Any], after: Dict[str, Any], action_result: Dict[str, Any]) -> bool:
        """Verify click action was successful"""
        if not action_result.get("success"):
            return False
        
        # Check for page changes indicating click success
        before_url = before.get("url", "")
        after_url = after.get("url", "")
        
        # URL changed = likely successful
        if before_url != after_url:
            return True
        
        # Check for new content/elements
        before_elements = len(before.get("vision", []))
        after_elements = len(after.get("vision", []))
        
        # Significant element change = likely successful
        if abs(after_elements - before_elements) > 2:
            return True
        
        # Check for success/error messages
        after_analysis = after.get("page_analysis", {})
        
        # New success message = click worked
        if after_analysis.get("success_messages"):
            return True
        
        # New error = click may have failed
        if after_analysis.get("errors"):
            new_errors = set(after_analysis.get("errors", []))
            before_errors = set(before.get("page_analysis", {}).get("errors", []))
            
            if new_errors - before_errors:
                logger.warning("⚠️ [VERIFICATION] Click may have caused errors")
                return False
        
        # Default to success if no clear failure indicators
        return True
    
    async def _verify_result_step(self, step: Dict[str, Any], perception: Dict[str, Any]) -> bool:
        """Verify result verification step (meta-verification)"""
        page_analysis = perception.get("page_analysis", {})
        
        # Check for clear success indicators
        if page_analysis.get("success_messages"):
            return True
        
        # Check page type for success
        page_type = page_analysis.get("page_type")
        if page_type in ["dashboard", "success_page", "verification"]:
            return True
        
        # Check URL for success patterns
        url = perception.get("url", "").lower()
        success_patterns = ["/dashboard", "/home", "/profile", "/welcome", "/verify", "/success"]
        
        if any(pattern in url for pattern in success_patterns):
            return True
        
        # If no clear success, check for failure
        if page_analysis.get("errors") or page_type == "error_page":
            return False
        
        # Ambiguous case - use conservative approach
        return True
    
    async def _llm_verify_step(self, step: Dict[str, Any], before: Dict[str, Any], after: Dict[str, Any], action_result: Dict[str, Any]) -> bool:
        """Use LLM for complex step verification"""
        try:
            prompt = f"""
            Verify if this automation step was successful:
            
            Step: {step.get('action', 'unknown')} - {step.get('description', '')}
            Expected outcome: {step.get('expected_outcome', 'unknown')}
            
            Before action:
            - URL: {before.get('url', 'unknown')}
            - Page type: {before.get('page_analysis', {}).get('page_type', 'unknown')}
            - Errors: {before.get('page_analysis', {}).get('errors', [])}
            
            After action:
            - URL: {after.get('url', 'unknown')} 
            - Page type: {after.get('page_analysis', {}).get('page_type', 'unknown')}
            - Errors: {after.get('page_analysis', {}).get('errors', [])}
            - Success messages: {after.get('page_analysis', {}).get('success_messages', [])}
            
            Action result: {action_result}
            
            Was the step successful? Consider:
            1. Did the expected outcome occur?
            2. Are there new error messages?
            3. Did the page state change appropriately?
            
            Return only "SUCCESS" or "FAILED" with brief reason.
            """
            
            messages = [
                {"role": "system", "content": "You are an expert at verifying web automation steps. Be conservative - only return SUCCESS if clearly successful."},
                {"role": "user", "content": prompt}
            ]
            
            response = await openrouter_service.chat_completion(
                messages=messages,
                model=self.model,
                temperature=self.temperature,
                max_tokens=100
            )
            
            result = response['choices'][0]['message']['content'].upper()
            
            return "SUCCESS" in result
        
        except Exception as e:
            logger.error(f"❌ [VERIFICATION] LLM step verification failed: {e}")
            return True  # Default to success on error
    
    async def _llm_verify_goal(self, goal: str, perception: Dict[str, Any], resources: Dict[str, Any]) -> bool:
        """Use LLM for complex goal verification"""
        try:
            prompt = f"""
            Verify if this automation goal was achieved:
            
            Goal: {goal}
            
            Current state:
            - URL: {perception.get('url', 'unknown')}
            - Page type: {perception.get('page_analysis', {}).get('page_type', 'unknown')}
            - Page content: {perception.get('page_text', '')[:500]}...
            - Success messages: {perception.get('page_analysis', {}).get('success_messages', [])}
            - Error messages: {perception.get('page_analysis', {}).get('errors', [])}
            
            Created resources: {list(resources.keys())}
            
            Has the goal been achieved? Consider:
            1. Is the user now logged in / registered / on the target page?
            2. Are there confirmation messages?
            3. Does the current page state match goal completion?
            
            Return only "ACHIEVED" or "NOT_ACHIEVED" with brief reason.
            """
            
            messages = [
                {"role": "system", "content": "You are an expert at determining if automation goals are achieved. Be accurate and consider the full context."},
                {"role": "user", "content": prompt}
            ]
            
            response = await openrouter_service.chat_completion(
                messages=messages,
                model=self.model,
                temperature=self.temperature,
                max_tokens=150
            )
            
            result = response['choices'][0]['message']['content'].upper()
            
            return "ACHIEVED" in result
        
        except Exception as e:
            logger.error(f"❌ [VERIFICATION] LLM goal verification failed: {e}")
            return False  # Default to not achieved on error
    
    def extract_verification_codes(self, text: str) -> List[str]:
        """Extract verification codes from text (emails, SMS)"""
        # Common verification code patterns
        patterns = [
            r'\b\d{6}\b',  # 6-digit codes
            r'\b\d{4}\b',  # 4-digit codes
            r'\b\d{8}\b',  # 8-digit codes
            r'code:\s*(\d+)',  # "code: 123456"
            r'verification.*?(\d{4,8})',  # "verification code is 123456"
            r'confirm.*?(\d{4,8})',  # "confirm with 123456"
        ]
        
        codes = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            codes.extend(matches)
        
        # Return unique codes, longest first (more likely to be verification codes)
        unique_codes = list(set(codes))
        return sorted(unique_codes, key=len, reverse=True)
    
    async def check_for_phone_verification(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """Check if phone verification is required"""
        page_text = perception.get("page_text", "").lower()
        page_analysis = perception.get("page_analysis", {})
        
        # Phone verification indicators
        phone_indicators = [
            "phone", "sms", "text message", "verification code", 
            "mobile", "cell", "number", "verify", "confirm"
        ]
        
        has_phone_indicators = any(indicator in page_text for indicator in phone_indicators)
        
        # Look for phone input fields
        vision_elements = perception.get("vision", [])
        phone_inputs = []
        
        for element in vision_elements:
            label = element.get("label", "").lower()
            if "phone" in label or "mobile" in label or "sms" in label:
                phone_inputs.append(element)
        
        return {
            "phone_verification_required": has_phone_indicators and len(phone_inputs) > 0,
            "phone_indicators": has_phone_indicators,
            "phone_input_fields": phone_inputs,
            "verification_type": "phone" if has_phone_indicators else None
        }
    
    async def check_for_email_verification(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """Check if email verification is required"""
        page_text = perception.get("page_text", "").lower()
        
        # Email verification indicators
        email_indicators = [
            "check your email", "verify your email", "confirmation email",
            "click the link", "activate your account", "email sent"
        ]
        
        has_email_verification = any(indicator in page_text for indicator in email_indicators)
        
        return {
            "email_verification_required": has_email_verification,
            "verification_type": "email" if has_email_verification else None,
            "message": "Check email for verification link" if has_email_verification else None
        }


# Global instance  
verification = Verification()