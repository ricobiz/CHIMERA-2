"""
Perception - State capture and analysis
Integrates with existing browser_automation_service and scene_builder_service
"""

import logging
from typing import Dict, Any, List, Optional

from ..services.browser_automation_service import browser_service
from ..services.scene_builder_service import scene_builder_service

logger = logging.getLogger(__name__)

class Perception:
    """
    Perception system that captures and analyzes current page state.
    Uses existing services for DOM collection, vision, and scene building.
    """
    
    def __init__(self):
        self.browser_service = browser_service
        self.scene_builder = scene_builder_service
    
    async def capture_state(self, session_id: str) -> Dict[str, Any]:
        """
        Capture complete page state including visual and structural information.
        
        Args:
            session_id: Browser session identifier
            
        Returns:
            Comprehensive state information
        """
        try:
            if session_id not in self.browser_service.sessions:
                raise ValueError(f"Session {session_id} not found")
            
            page = self.browser_service.sessions[session_id]['page']
            
            # 1. Capture screenshot
            screenshot_base64 = await self.browser_service.capture_screenshot(session_id)
            
            # 2. Inject grid and collect DOM data
            await self.browser_service._inject_grid_overlay(page)
            dom_data = await self.browser_service._collect_dom_clickables(page)
            
            # 3. Augment with vision
            vision_elements = await self.browser_service._augment_with_vision(screenshot_base64, dom_data)
            
            # 4. Build scene JSON
            scene = await self.scene_builder.build_scene(
                page=page,
                dom_data=dom_data,
                vision_elements=vision_elements,
                session_id=session_id
            )
            
            # 5. Extract page text for analysis
            page_text = await page.evaluate("() => document.body?.innerText || ''")
            
            # 6. Get current URL and title
            current_url = page.url
            title = await page.title()
            
            # 7. Check for loading state
            loading_status = await self.browser_service.is_page_loading(page)
            
            # 8. Detect common page elements
            page_analysis = await self._analyze_page_content(page)
            
            state = {
                # Visual information
                "screenshot_base64": screenshot_base64,
                "screenshot_id": f"perception_{session_id}_{int(scene.get('ts', 0))}",
                
                # Structural information  
                "vision": vision_elements,
                "scene": scene,
                "dom_data": dom_data,
                
                # Page information
                "url": current_url,
                "title": title,
                "page_text": page_text[:2000],  # Limit size
                
                # State analysis
                "loading": loading_status,
                "page_analysis": page_analysis,
                
                # Meta information
                "viewport": scene.get("viewport", [1280, 800]),
                "grid": {"rows": self.browser_service.grid_rows, "cols": self.browser_service.grid_cols},
                "timestamp": scene.get("ts"),
                
                # Summary for quick access
                "summary": self._create_summary(scene, page_analysis, current_url)
            }
            
            logger.info(f"📸 [PERCEPTION] Captured state: {len(vision_elements)} elements, {current_url}")
            return state
            
        except Exception as e:
            logger.error(f"❌ [PERCEPTION] State capture failed: {e}")
            return {
                "error": str(e),
                "screenshot_base64": None,
                "vision": [],
                "scene": {},
                "url": "unknown",
                "summary": f"Perception failed: {e}"
            }
    
    async def _analyze_page_content(self, page) -> Dict[str, Any]:
        """Analyze page content for common patterns and elements"""
        try:
            analysis = {
                "forms": [],
                "buttons": [],
                "inputs": [],
                "links": [],
                "errors": [],
                "success_messages": [],
                "page_type": "unknown"
            }
            
            # Detect forms
            forms = await page.query_selector_all("form")
            for form in forms:
                form_info = await page.evaluate("""(form) => {
                    const inputs = Array.from(form.querySelectorAll('input, textarea, select'));
                    return {
                        action: form.action || '',
                        method: form.method || 'GET',
                        input_count: inputs.length,
                        input_types: inputs.map(i => i.type || i.tagName.toLowerCase())
                    };
                }""", form)
                analysis["forms"].append(form_info)
            
            # Detect buttons
            buttons = await page.query_selector_all("button, input[type='button'], input[type='submit']")
            for button in buttons:
                button_text = await button.inner_text()
                if button_text:
                    analysis["buttons"].append(button_text.strip()[:50])
            
            # Detect input fields
            inputs = await page.query_selector_all("input, textarea, select")
            for input_elem in inputs:
                input_info = await page.evaluate("""(input) => {
                    return {
                        type: input.type || input.tagName.toLowerCase(),
                        name: input.name || '',
                        placeholder: input.placeholder || '',
                        required: input.required || false
                    };
                }""", input_elem)
                analysis["inputs"].append(input_info)
            
            # Detect links
            links = await page.query_selector_all("a[href]")
            link_count = len(links)
            analysis["links"] = [{"count": link_count}]
            
            # Detect error messages
            error_selectors = [
                "[class*='error']", "[class*='danger']", "[class*='invalid']",
                ".alert-danger", ".error-message", ".field-error"
            ]
            for selector in error_selectors:
                elements = await page.query_selector_all(selector)
                for elem in elements:
                    is_visible = await elem.is_visible()
                    if is_visible:
                        text = await elem.inner_text()
                        if text.strip():
                            analysis["errors"].append(text.strip()[:100])
            
            # Detect success messages
            success_selectors = [
                "[class*='success']", "[class*='confirm']", ".alert-success"
            ]
            for selector in success_selectors:
                elements = await page.query_selector_all(selector)
                for elem in elements:
                    is_visible = await elem.is_visible()
                    if is_visible:
                        text = await elem.inner_text()
                        if text.strip():
                            analysis["success_messages"].append(text.strip()[:100])
            
            # Determine page type
            analysis["page_type"] = self._determine_page_type(analysis, page.url)
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ [PERCEPTION] Page analysis failed: {e}")
            return {
                "forms": [], "buttons": [], "inputs": [], "links": [],
                "errors": [], "success_messages": [], "page_type": "unknown"
            }
    
    def _determine_page_type(self, analysis: Dict[str, Any], url: str) -> str:
        """Determine the type of page based on content analysis"""
        url_lower = url.lower()
        
        # Check URL patterns first
        if "/login" in url_lower or "/signin" in url_lower:
            return "login"
        elif "/register" in url_lower or "/signup" in url_lower:
            return "registration"
        elif "/verify" in url_lower or "/confirm" in url_lower:
            return "verification"
        elif "/dashboard" in url_lower or "/home" in url_lower or "/profile" in url_lower:
            return "dashboard"
        
        # Check form patterns
        forms = analysis.get("forms", [])
        if forms:
            input_types = []
            for form in forms:
                input_types.extend(form.get("input_types", []))
            
            # Registration indicators
            if len(input_types) >= 4 and any(t in input_types for t in ["email", "password"]):
                if input_types.count("password") >= 2:  # Password confirmation
                    return "registration"
            
            # Login indicators
            if len(input_types) == 2 and "email" in input_types and "password" in input_types:
                return "login"
        
        # Check button text
        buttons = analysis.get("buttons", [])
        button_text = " ".join(buttons).lower()
        
        if any(keyword in button_text for keyword in ["register", "sign up", "create account"]):
            return "registration"
        elif any(keyword in button_text for keyword in ["login", "sign in", "log in"]):
            return "login"
        
        # Check for success/error indicators
        if analysis.get("success_messages"):
            return "success_page"
        elif analysis.get("errors"):
            return "error_page"
        
        return "content"
    
    def _create_summary(self, scene: Dict[str, Any], page_analysis: Dict[str, Any], url: str) -> str:
        """Create human-readable summary of current state"""
        elements = scene.get("elements", [])
        antibot = scene.get("antibot", {})
        
        summary_parts = [
            f"Page: {page_analysis.get('page_type', 'unknown')} at {url}",
            f"Elements: {len(elements)} interactive elements found"
        ]
        
        # Form information
        forms = page_analysis.get("forms", [])
        if forms:
            input_count = sum(form.get("input_count", 0) for form in forms)
            summary_parts.append(f"Forms: {len(forms)} form(s) with {input_count} total inputs")
        
        # Button information
        buttons = page_analysis.get("buttons", [])
        if buttons:
            summary_parts.append(f"Buttons: {', '.join(buttons[:3])}")
        
        # Error/success information
        errors = page_analysis.get("errors", [])
        if errors:
            summary_parts.append(f"Errors: {len(errors)} error message(s)")
        
        success_msgs = page_analysis.get("success_messages", [])
        if success_msgs:
            summary_parts.append(f"Success: {len(success_msgs)} success message(s)")
        
        # Antibot information
        if antibot.get("present"):
            summary_parts.append(f"Antibot: {antibot.get('type')} detected")
        
        return "; ".join(summary_parts)
    
    async def get_element_at_cell(self, session_id: str, cell: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about element at specific grid cell"""
        try:
            state = await self.capture_state(session_id)
            vision_elements = state.get("vision", [])
            
            for element in vision_elements:
                if element.get("cell") == cell:
                    return element
            
            return None
            
        except Exception as e:
            logger.error(f"❌ [PERCEPTION] Element lookup failed: {e}")
            return None
    
    async def find_elements_by_type(self, session_id: str, element_type: str) -> List[Dict[str, Any]]:
        """Find all elements of specific type"""
        try:
            state = await self.capture_state(session_id)
            vision_elements = state.get("vision", [])
            
            matching_elements = [
                elem for elem in vision_elements 
                if elem.get("type", "").lower() == element_type.lower()
            ]
            
            return matching_elements
            
        except Exception as e:
            logger.error(f"❌ [PERCEPTION] Element search failed: {e}")
            return []
    
    async def detect_page_changes(self, session_id: str, previous_state: Dict[str, Any]) -> Dict[str, Any]:
        """Detect changes between current and previous page state"""
        try:
            current_state = await self.capture_state(session_id)
            
            changes = {
                "url_changed": current_state.get("url") != previous_state.get("url"),
                "elements_changed": len(current_state.get("vision", [])) != len(previous_state.get("vision", [])),
                "new_errors": [],
                "new_success": [],
                "page_type_changed": False
            }
            
            # Check for new error messages
            current_errors = set(current_state.get("page_analysis", {}).get("errors", []))
            previous_errors = set(previous_state.get("page_analysis", {}).get("errors", []))
            changes["new_errors"] = list(current_errors - previous_errors)
            
            # Check for new success messages
            current_success = set(current_state.get("page_analysis", {}).get("success_messages", []))
            previous_success = set(previous_state.get("page_analysis", {}).get("success_messages", []))
            changes["new_success"] = list(current_success - previous_success)
            
            # Check page type change
            current_type = current_state.get("page_analysis", {}).get("page_type")
            previous_type = previous_state.get("page_analysis", {}).get("page_type")
            changes["page_type_changed"] = current_type != previous_type
            
            return changes
            
        except Exception as e:
            logger.error(f"❌ [PERCEPTION] Change detection failed: {e}")
            return {"error": str(e)}


# Global instance
perception = Perception()