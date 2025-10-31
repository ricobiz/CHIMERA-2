"""
Execution - Browser action execution
Integrates with existing browser_automation_service for reliable action execution
"""

import logging
import asyncio
import random
from typing import Dict, Any, Optional

from services.browser_automation_service import browser_service

logger = logging.getLogger(__name__)

class Execution:
    """
    Execution engine for browser actions.
    Uses existing browser_automation_service with enhanced reliability and error handling.
    """
    
    def __init__(self):
        self.browser_service = browser_service
    
    async def execute(
        self, 
        action: Dict[str, Any], 
        session_id: str, 
        resources: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute browser action with comprehensive error handling and retries.
        
        Args:
            action: Action to execute with type and parameters
            session_id: Browser session identifier  
            resources: Available resources (email, password, etc.)
            
        Returns:
            Execution result with success status and details
        """
        try:
            action_type = action.get("type", "").lower()
            logger.info(f"⚡ [EXECUTION] Executing {action_type}")
            
            # Ensure page is ready
            await self._ensure_page_ready(session_id)
            
            # Execute specific action
            if action_type == "navigate":
                return await self._execute_navigate(action, session_id)
            
            elif action_type == "type_at_cell":
                return await self._execute_type_at_cell(action, session_id, resources)
            
            elif action_type == "click_cell":
                return await self._execute_click_cell(action, session_id)
            
            elif action_type == "wait":
                return await self._execute_wait(action)
            
            elif action_type == "verification_success":
                return await self._execute_verification_success(action)
            
            elif action_type == "verification_failed":
                return await self._execute_verification_failed(action)
            
            elif action_type == "fill_detected_fields":
                return await self._execute_fill_form(action, session_id, resources)
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown action type: {action_type}",
                    "action": action
                }
        
        except Exception as e:
            logger.error(f"❌ [EXECUTION] Action failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": action
            }
    
    async def _ensure_page_ready(self, session_id: str, timeout_seconds: int = 10):
        """Ensure page is fully loaded and ready for interaction"""
        try:
            if session_id not in self.browser_service.sessions:
                raise ValueError(f"Session {session_id} not found")
            
            page = self.browser_service.sessions[session_id]['page']
            
            # Wait for page to be ready
            await self.browser_service.wait_for_page_ready(page, timeout_ms=timeout_seconds * 1000)
            
            # Additional human-like delay
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
        except Exception as e:
            logger.warning(f"⚠️ [EXECUTION] Page ready check failed: {e}")
    
    async def _execute_navigate(self, action: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Execute navigation action"""
        try:
            url = action.get("url", "")
            if not url:
                return {"success": False, "error": "No URL specified for navigation"}
            
            logger.info(f"🌐 [EXECUTION] Navigating to {url}")
            
            result = await self.browser_service.navigate(session_id, url)
            
            if result.get("success"):
                # Capture screenshot after navigation
                screenshot = await self.browser_service.capture_screenshot(session_id)
                
                return {
                    "success": True,
                    "url": result.get("url"),
                    "title": result.get("title"),
                    "screenshot": screenshot,
                    "action": "navigate"
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Navigation failed"),
                    "action": "navigate"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Navigation error: {e}",
                "action": "navigate"
            }
    
    async def _execute_type_at_cell(self, action: Dict[str, Any], session_id: str, resources: Dict[str, Any]) -> Dict[str, Any]:
        """Execute typing at specific grid cell"""
        try:
            cell = action.get("cell", "")
            text = action.get("text", "")
            field = action.get("field", "")
            
            if not cell:
                return {"success": False, "error": "No cell specified for typing"}
            
            if not text:
                return {"success": False, "error": "No text specified for typing"}
            
            logger.info(f"⌨️ [EXECUTION] Typing at {cell}: {text[:30]}...")
            
            # Execute typing with human-like behavior
            result = await self.browser_service.type_at_cell(session_id, cell, text, human_like=True)
            
            if result.get("success"):
                return {
                    "success": True,
                    "cell": cell,
                    "text": text,
                    "field": field,
                    "screenshot": result.get("screenshot"),
                    "action": "type_at_cell"
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Typing failed"),
                    "cell": cell,
                    "action": "type_at_cell"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Typing error: {e}",
                "action": "type_at_cell"
            }
    
    async def _execute_click_cell(self, action: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Execute click at specific grid cell"""
        try:
            cell = action.get("cell", "")
            
            if not cell:
                return {"success": False, "error": "No cell specified for clicking"}
            
            logger.info(f"👆 [EXECUTION] Clicking at {cell}")
            
            # Execute click with human-like behavior
            result = await self.browser_service.click_cell(session_id, cell, human_like=True)
            
            if result.get("success"):
                # Wait for potential page changes
                await asyncio.sleep(random.uniform(1.0, 2.5))
                
                return {
                    "success": True,
                    "cell": cell,
                    "coordinates": result.get("coordinates"),
                    "screenshot": result.get("screenshot"),
                    "action": "click_cell"
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Click failed"),
                    "cell": cell,
                    "action": "click_cell"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Click error: {e}",
                "action": "click_cell"
            }
    
    async def _execute_wait(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute wait action"""
        try:
            duration_ms = action.get("duration_ms", 2000)
            duration_seconds = duration_ms / 1000.0
            
            logger.info(f"⏱️ [EXECUTION] Waiting {duration_seconds}s")
            
            await asyncio.sleep(duration_seconds)
            
            return {
                "success": True,
                "duration_ms": duration_ms,
                "action": "wait"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Wait error: {e}",
                "action": "wait"
            }
    
    async def _execute_verification_success(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful verification"""
        try:
            indicators = action.get("indicators", {})
            confidence = action.get("confidence", 1.0)
            
            logger.info(f"✅ [EXECUTION] Verification successful (confidence: {confidence})")
            
            return {
                "success": True,
                "verification_result": "success",
                "indicators": indicators,
                "confidence": confidence,
                "action": "verification_success"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Verification success handling error: {e}",
                "action": "verification_success"
            }
    
    async def _execute_verification_failed(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed verification"""
        try:
            reason = action.get("reason", "Verification failed")
            next_action = action.get("next_action", "retry")
            
            logger.warning(f"❌ [EXECUTION] Verification failed: {reason}")
            
            return {
                "success": False,
                "verification_result": "failed", 
                "reason": reason,
                "next_action": next_action,
                "action": "verification_failed"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Verification failure handling error: {e}",
                "action": "verification_failed"
            }
    
    async def _execute_fill_form(self, action: Dict[str, Any], session_id: str, resources: Dict[str, Any]) -> Dict[str, Any]:
        """Fill entire form with available data"""
        try:
            logger.info("📝 [EXECUTION] Filling detected form fields")
            
            # Get current page state to find form fields
            from automation.perception import perception
            state = await perception.capture_state(session_id)
            
            vision_elements = state.get("vision", [])
            form_fields = [elem for elem in vision_elements if elem.get("type", "").lower() in ["textbox", "input", "textarea"]]
            
            filled_count = 0
            errors = []
            
            for field_element in form_fields:
                try:
                    cell = field_element.get("cell")
                    label = field_element.get("label", "").lower()
                    
                    # Match field to available data
                    text_to_fill = self._match_field_to_data(label, resources)
                    
                    if text_to_fill and cell:
                        type_result = await self.browser_service.type_at_cell(session_id, cell, text_to_fill, human_like=True)
                        
                        if type_result.get("success"):
                            filled_count += 1
                            await asyncio.sleep(random.uniform(0.5, 1.5))  # Human delay between fields
                        else:
                            errors.append(f"Failed to fill {label}: {type_result.get('error')}")
                    
                except Exception as field_error:
                    errors.append(f"Error filling field {field_element.get('label', 'unknown')}: {field_error}")
            
            # Capture final screenshot
            screenshot = await self.browser_service.capture_screenshot(session_id)
            
            return {
                "success": filled_count > 0,
                "fields_filled": filled_count,
                "total_fields": len(form_fields),
                "errors": errors,
                "screenshot": screenshot,
                "action": "fill_form"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Form filling error: {e}",
                "action": "fill_form"
            }
    
    def _match_field_to_data(self, field_label: str, resources: Dict[str, Any]) -> Optional[str]:
        """Match form field label to available resource data"""
        label_lower = field_label.lower()
        
        # Email fields
        if "email" in label_lower:
            return resources.get("email")
        
        # Password fields
        if "password" in label_lower:
            return resources.get("password")
        
        # Name fields  
        if "first" in label_lower and "name" in label_lower:
            return resources.get("first_name")
        
        if "last" in label_lower and "name" in label_lower:
            return resources.get("last_name")
        
        if "name" in label_lower and "first" not in label_lower and "last" not in label_lower:
            # Generic name field - use first name
            return resources.get("first_name")
        
        # Username fields
        if "username" in label_lower or "user" in label_lower:
            return resources.get("username") or resources.get("email")
        
        # Phone fields
        if "phone" in label_lower:
            return resources.get("phone_number")
        
        # Birthday/date fields
        if "birth" in label_lower or "date" in label_lower:
            return resources.get("birthday")
        
        # Address fields
        if "address" in label_lower:
            return resources.get("address")
        
        if "city" in label_lower:
            return resources.get("city")
        
        if "state" in label_lower:
            return resources.get("state")
        
        if "zip" in label_lower or "postal" in label_lower:
            return resources.get("postal_code")
        
        return None
    
    async def execute_captcha_solve(self, session_id: str) -> Dict[str, Any]:
        """Execute CAPTCHA solving if present"""
        try:
            logger.info("🔍 [EXECUTION] Checking for CAPTCHA")
            
            result = await self.browser_service.detect_and_solve_captcha(session_id)
            
            return {
                "success": result.get("success", False),
                "captcha_solved": result.get("success", False),
                "message": result.get("message", "No CAPTCHA detected"),
                "screenshot": result.get("screenshot"),
                "action": "solve_captcha"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"CAPTCHA solving error: {e}",
                "action": "solve_captcha"
            }
    
    async def execute_scroll(self, session_id: str, direction: str = "down", amount: int = 400) -> Dict[str, Any]:
        """Execute scrolling action"""
        try:
            dy = amount if direction == "down" else -amount
            
            logger.info(f"📜 [EXECUTION] Scrolling {direction} by {amount}px")
            
            result = await self.browser_service.scroll(session_id, dx=0, dy=dy)
            
            if result.get("error"):
                return {
                    "success": False,
                    "error": result["error"],
                    "action": "scroll"
                }
            
            return {
                "success": True,
                "direction": direction,
                "amount": amount,
                "screenshot": result.get("screenshot_base64"),
                "action": "scroll"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Scroll error: {e}",
                "action": "scroll"
            }


# Global instance
execution = Execution()