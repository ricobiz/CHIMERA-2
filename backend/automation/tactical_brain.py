"""
Tactical Brain - Step-level decision making
Uses Qwen2.5-72B for tactical decisions within the execution loop
"""

import json
import logging
from typing import Dict, Any, List, Optional

from ..services.openrouter_service import openrouter_service

logger = logging.getLogger(__name__)

class TacticalBrain:
    """
    Tactical decision maker for individual steps.
    Decides exactly what action to take based on current step, perception, and context.
    """
    
    def __init__(self):
        self.model = "qwen/qwen2.5-72b-instruct"  # Fast tactical decisions
        self.temperature = 0.1  # Low for consistent decisions
        self.max_tokens = 1500
    
    async def decide(
        self,
        step: Dict[str, Any],
        perception: Dict[str, Any], 
        resources: Dict[str, Any],
        history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make tactical decision for current step.
        
        Args:
            step: Current step from plan
            perception: Current page state (vision, DOM, etc.)
            resources: Available resources (email, password, etc.)
            history: Recent execution history
            
        Returns:
            Decision with action, tool_call, or reasoning
        """
        try:
            # Extract step information
            step_action = step.get("action", "").upper()
            step_field = step.get("field")
            step_target = step.get("target")
            step_data_key = step.get("data_key")
            
            logger.info(f"🧠 [TACTICAL] Deciding for step: {step_action}")
            
            # Quick decisions for simple actions
            if step_action in ["NAVIGATE", "WAIT"]:
                return self._handle_simple_action(step)
            
            # Smart decisions for complex actions
            if step_action == "TYPE":
                return await self._decide_type_action(step, perception, resources)
            
            elif step_action == "CLICK":
                return await self._decide_click_action(step, perception)
            
            elif step_action == "VERIFY_RESULT":
                return await self._decide_verification(step, perception, resources)
            
            elif step_action == "ANALYZE_FORM":
                return await self._decide_form_analysis(perception)
            
            elif step_action == "FILL_FORM":
                return await self._decide_form_filling(perception, resources)
            
            elif step_action == "SUBMIT_FORM":
                return await self._decide_form_submit(perception)
            
            else:
                # Use LLM for unknown actions
                return await self._llm_decision(step, perception, resources, history)
        
        except Exception as e:
            logger.error(f"❌ [TACTICAL] Decision error: {e}")
            return {
                "action": None,
                "error": str(e),
                "reasoning": "Decision failed due to error"
            }
    
    def _handle_simple_action(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Handle simple actions that don't need complex decisions"""
        step_action = step.get("action", "").upper()
        
        if step_action == "NAVIGATE":
            return {
                "action": {
                    "type": "navigate",
                    "url": step.get("target", "")
                },
                "reasoning": "Direct navigation to target URL"
            }
        
        elif step_action == "WAIT":
            return {
                "action": {
                    "type": "wait",
                    "duration_ms": step.get("duration_ms", 2000)
                },
                "reasoning": "Wait for specified duration"
            }
        
        return {"action": None, "reasoning": "Unknown simple action"}
    
    async def _decide_type_action(
        self, 
        step: Dict[str, Any], 
        perception: Dict[str, Any], 
        resources: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Decide how to type text into a field"""
        
        step_field = step.get("field")
        step_data_key = step.get("data_key")
        step_target = step.get("target", {})
        
        # Get the text to type
        text_to_type = ""
        if step_data_key and step_data_key in resources:
            text_to_type = str(resources[step_data_key])
        elif isinstance(step_target, str):
            text_to_type = step_target
        elif isinstance(step_target, dict) and "value" in step_target:
            text_to_type = step_target["value"]
        
        if not text_to_type:
            # Need to generate or request data
            return {
                "tool_call": {
                    "name": "generate_field_data",
                    "params": {
                        "field": step_field,
                        "data_key": step_data_key
                    }
                },
                "reasoning": f"Need to generate data for field: {step_field}"
            }
        
        # Find target element
        vision_elements = perception.get("vision", [])
        target_cell = self._find_target_element(step_target, step_field, vision_elements, "textbox")
        
        if target_cell:
            return {
                "action": {
                    "type": "type_at_cell",
                    "cell": target_cell,
                    "text": text_to_type,
                    "field": step_field
                },
                "reasoning": f"Type '{text_to_type[:20]}...' into field {step_field} at {target_cell}"
            }
        else:
            # Use LLM to find element
            return await self._llm_find_element(step, perception, "input field")
    
    async def _decide_click_action(self, step: Dict[str, Any], perception: Dict[str, Any]) -> Dict[str, Any]:
        """Decide how to click an element"""
        
        step_target = step.get("target", {})
        vision_elements = perception.get("vision", [])
        
        # Find target element
        target_cell = self._find_target_element(step_target, None, vision_elements, "button")
        
        if target_cell:
            return {
                "action": {
                    "type": "click_cell", 
                    "cell": target_cell
                },
                "reasoning": f"Click element at {target_cell}"
            }
        else:
            # Use LLM to find clickable element
            return await self._llm_find_element(step, perception, "clickable element")
    
    async def _decide_verification(
        self, 
        step: Dict[str, Any], 
        perception: Dict[str, Any], 
        resources: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Decide how to verify step completion"""
        
        # Check for common success/failure indicators
        page_text = perception.get("page_text", "").lower()
        current_url = perception.get("url", "")
        
        # Success indicators
        success_patterns = [
            "success", "welcome", "registered", "logged in", "dashboard",
            "account created", "verification", "confirm", "complete"
        ]
        
        # Failure indicators
        failure_patterns = [
            "error", "invalid", "failed", "wrong", "incorrect", "already exists",
            "try again", "please check"
        ]
        
        has_success = any(pattern in page_text for pattern in success_patterns)
        has_failure = any(pattern in page_text for pattern in failure_patterns)
        
        # URL change indicates potential success
        url_changed = "/login" not in current_url and "/register" not in current_url
        
        if has_success or url_changed:
            return {
                "action": {
                    "type": "verification_success",
                    "indicators": {
                        "success_text": has_success,
                        "url_changed": url_changed,
                        "current_url": current_url
                    }
                },
                "reasoning": "Verification successful based on page indicators"
            }
        
        elif has_failure:
            return {
                "action": {
                    "type": "verification_failed",
                    "reason": "Error indicators detected on page"
                },
                "reasoning": "Verification failed - error messages detected"
            }
        
        else:
            # Use LLM for complex verification
            return await self._llm_verification(step, perception, resources)
    
    async def _decide_form_analysis(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze form fields on current page"""
        vision_elements = perception.get("vision", [])
        
        # Find all form fields
        form_fields = []
        for element in vision_elements:
            if element.get("type", "").lower() in ["textbox", "input", "textarea"]:
                form_fields.append({
                    "cell": element.get("cell"),
                    "label": element.get("label", ""),
                    "type": element.get("type", ""),
                    "field_type": self._guess_field_type(element.get("label", ""))
                })
        
        return {
            "action": {
                "type": "form_analyzed",
                "fields": form_fields
            },
            "reasoning": f"Analyzed {len(form_fields)} form fields"
        }
    
    async def _decide_form_filling(self, perception: Dict[str, Any], resources: Dict[str, Any]) -> Dict[str, Any]:
        """Decide how to fill entire form"""
        # This would trigger a sequence of TYPE actions
        # For now, return a simple action that can be expanded
        
        return {
            "action": {
                "type": "fill_detected_fields",
                "resources": resources
            },
            "reasoning": "Fill all detected form fields with available data"
        }
    
    async def _decide_form_submit(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """Find and click submit button"""
        vision_elements = perception.get("vision", [])
        
        # Look for submit buttons
        submit_patterns = ["submit", "register", "sign up", "create", "continue", "next"]
        
        for element in vision_elements:
            label = element.get("label", "").lower()
            if element.get("type", "").lower() == "button" and any(pattern in label for pattern in submit_patterns):
                return {
                    "action": {
                        "type": "click_cell",
                        "cell": element.get("cell")
                    },
                    "reasoning": f"Click submit button: {element.get('label')}"
                }
        
        # Fallback: use LLM to find submit button
        return await self._llm_find_element(
            {"action": "CLICK", "target": {"by": "label", "value": "submit"}}, 
            perception, 
            "submit button"
        )
    
    def _find_target_element(
        self, 
        step_target: Any, 
        step_field: Optional[str], 
        vision_elements: List[Dict[str, Any]], 
        element_type: str
    ) -> Optional[str]:
        """
        Find target element in vision using various strategies.
        Returns cell identifier (e.g., "C7") if found.
        """
        
        if not vision_elements:
            return None
        
        # Strategy 1: Exact target match
        if isinstance(step_target, dict):
            target_by = step_target.get("by", "label")
            target_value = step_target.get("value", "").lower()
            
            for element in vision_elements:
                if target_by == "label" and target_value in element.get("label", "").lower():
                    return element.get("cell")
                elif target_by == "type" and element.get("type", "").lower() == target_value:
                    return element.get("cell")
        
        # Strategy 2: Field name match
        if step_field:
            field_lower = step_field.lower()
            for element in vision_elements:
                element_label = element.get("label", "").lower()
                if field_lower in element_label or element_label in field_lower:
                    return element.get("cell")
        
        # Strategy 3: Element type match (first available)
        type_mapping = {
            "textbox": ["textbox", "input", "textarea"],
            "button": ["button"],
            "link": ["link"]
        }
        
        target_types = type_mapping.get(element_type, [element_type])
        for element in vision_elements:
            if element.get("type", "").lower() in target_types:
                return element.get("cell")
        
        return None
    
    def _guess_field_type(self, label: str) -> str:
        """Guess field type from label"""
        label_lower = label.lower()
        
        if "email" in label_lower:
            return "email"
        elif "password" in label_lower:
            return "password"  
        elif "phone" in label_lower:
            return "phone"
        elif "name" in label_lower:
            if "first" in label_lower:
                return "first_name"
            elif "last" in label_lower:
                return "last_name"
            else:
                return "name"
        elif "birth" in label_lower or "age" in label_lower:
            return "birthday"
        elif "username" in label_lower:
            return "username"
        else:
            return "text"
    
    async def _llm_find_element(self, step: Dict[str, Any], perception: Dict[str, Any], element_description: str) -> Dict[str, Any]:
        """Use LLM to find element when simple strategies fail"""
        
        vision_summary = []
        for i, element in enumerate(perception.get("vision", [])[:10]):  # Limit to 10 elements
            vision_summary.append(f"{element.get('cell', 'X')}: {element.get('type', 'unknown')} - {element.get('label', 'no label')}")
        
        prompt = f"""
        I need to find {element_description} on this page to complete: {step.get('description', 'action')}
        
        Available elements:
        {chr(10).join(vision_summary)}
        
        Current URL: {perception.get('url', 'unknown')}
        
        Which cell should I target? Return ONLY the cell identifier (like A1, B2, etc.) or "NOT_FOUND" if no suitable element exists.
        """
        
        try:
            messages = [
                {"role": "system", "content": "You are an expert at identifying web elements. Return only the cell identifier or NOT_FOUND."},
                {"role": "user", "content": prompt}
            ]
            
            response = await openrouter_service.chat_completion(
                messages=messages,
                model=self.model,
                temperature=0.0,
                max_tokens=50
            )
            
            cell = response['choices'][0]['message']['content'].strip()
            
            if cell == "NOT_FOUND":
                return {
                    "action": None,
                    "error": f"Could not find {element_description}",
                    "reasoning": "LLM could not locate target element"
                }
            
            # Determine action type based on step
            step_action = step.get("action", "").upper()
            if step_action == "TYPE":
                return {
                    "action": {
                        "type": "type_at_cell",
                        "cell": cell,
                        "text": step.get("target", ""),
                        "field": step.get("field")
                    },
                    "reasoning": f"LLM identified target at {cell}"
                }
            else:  # CLICK
                return {
                    "action": {
                        "type": "click_cell",
                        "cell": cell
                    },
                    "reasoning": f"LLM identified clickable element at {cell}"
                }
        
        except Exception as e:
            logger.error(f"❌ [TACTICAL] LLM element finding failed: {e}")
            return {
                "action": None,
                "error": str(e),
                "reasoning": "LLM element finding failed"
            }
    
    async def _llm_verification(self, step: Dict[str, Any], perception: Dict[str, Any], resources: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM for complex verification scenarios"""
        
        prompt = f"""
        I need to verify if this step was successful: {step.get('description', 'unknown step')}
        
        Current page state:
        - URL: {perception.get('url', 'unknown')}
        - Page contains: {perception.get('page_text', '')[:500]}...
        
        Step expected outcome: {step.get('expected_outcome', 'unknown')}
        
        Was the step successful? Consider:
        1. Did the URL change appropriately?
        2. Are there success/error messages?
        3. Are expected elements now visible/hidden?
        4. Does the page state match expected outcome?
        
        Return JSON:
        {{
            "success": true/false,
            "confidence": 0.0-1.0,
            "reason": "explanation",
            "next_action": "continue|retry|wait_user|error"
        }}
        """
        
        try:
            messages = [
                {"role": "system", "content": "You are an expert at verifying web automation steps. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ]
            
            response = await openrouter_service.chat_completion(
                messages=messages,
                model=self.model,
                temperature=0.1,
                max_tokens=500
            )
            
            content = response['choices'][0]['message']['content']
            result = json.loads(content)
            
            if result.get("success"):
                return {
                    "action": {
                        "type": "verification_success",
                        "confidence": result.get("confidence", 0.7)
                    },
                    "reasoning": result.get("reason", "LLM verification successful")
                }
            else:
                return {
                    "action": {
                        "type": "verification_failed",
                        "reason": result.get("reason", "LLM verification failed"),
                        "next_action": result.get("next_action", "retry")
                    },
                    "reasoning": f"Verification failed: {result.get('reason')}"
                }
        
        except Exception as e:
            logger.error(f"❌ [TACTICAL] LLM verification failed: {e}")
            return {
                "action": {
                    "type": "verification_success",  # Default to success on error
                    "confidence": 0.5
                },
                "reasoning": "Verification error, assuming success"
            }
    
    async def _llm_decision(self, step: Dict[str, Any], perception: Dict[str, Any], resources: Dict[str, Any], history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Full LLM decision for complex scenarios"""
        
        # This would be used for very complex decision making
        # For now, return a simple response
        return {
            "action": None,
            "reasoning": "Complex LLM decision not yet implemented",
            "error": "Unknown action type"
        }


# Global instance
tactical_brain = TacticalBrain()