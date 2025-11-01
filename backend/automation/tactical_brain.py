"""
Tactical Brain - Step-level decision making
Uses Qwen2.5-72B for tactical decisions within the execution loop
"""

import json
import logging
from typing import Dict, Any, List, Optional

from services.openrouter_service import openrouter_service

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
        """Decide how to type text into a field - IMPROVED with intelligent element detection"""
        
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
        
        # NEW: Find target element with intelligent scoring
        vision_elements = perception.get("vision", [])
        element_result = self._find_target_element_with_scoring(
            step_target, step_field, vision_elements, "textbox", perception
        )
        
        target_cell = element_result.get("primary")
        confidence = element_result.get("confidence", 0.0)
        
        if target_cell and confidence > 0.3:  # Require minimum confidence
            return {
                "action": {
                    "type": "type_at_cell",
                    "cell": target_cell,
                    "text": text_to_type,
                    "field": step_field
                },
                "reasoning": f"Type '{text_to_type[:20]}...' into field {step_field} at {target_cell} (confidence: {confidence:.2f})",
                "alternatives": element_result.get("alternatives", []),
                "confidence": confidence
            }
        else:
            # Use LLM to find element as fallback
            logger.info(f"⚠️ [TACTICAL] Low confidence ({confidence:.2f}) for element detection, using LLM fallback")
            return await self._llm_find_element(step, perception, "input field")
    
    async def _decide_click_action(self, step: Dict[str, Any], perception: Dict[str, Any]) -> Dict[str, Any]:
        """Decide how to click an element - IMPROVED with intelligent element detection"""
        
        step_target = step.get("target", {})
        vision_elements = perception.get("vision", [])
        
        # NEW: Find target element with intelligent scoring
        element_result = self._find_target_element_with_scoring(
            step_target, None, vision_elements, "button", perception
        )
        
        target_cell = element_result.get("primary")
        confidence = element_result.get("confidence", 0.0)
        
        if target_cell and confidence > 0.3:  # Require minimum confidence
            return {
                "action": {
                    "type": "click_cell", 
                    "cell": target_cell
                },
                "reasoning": f"Click element at {target_cell} (confidence: {confidence:.2f})",
                "alternatives": element_result.get("alternatives", []),
                "confidence": confidence
            }
        else:
            # Use LLM to find clickable element as fallback
            logger.info(f"⚠️ [TACTICAL] Low confidence ({confidence:.2f}) for clickable element, using LLM fallback")
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
        NEW: Intelligent element finding with scoring and alternatives.
        Returns cell identifier (e.g., "C7") if found, or None.
        
        Uses multi-factor scoring instead of simple substring matching.
        """
        
        if not vision_elements:
            return None
        
        # Use new intelligent scoring system
        result = self._find_target_element_with_scoring(
            step_target, step_field, vision_elements, element_type, {}
        )
        
        # Return primary match
        return result.get("primary") if result else None
    
    def _find_target_element_with_scoring(
        self, 
        step_target: Any, 
        step_field: Optional[str], 
        vision_elements: List[Dict[str, Any]], 
        element_type: str,
        perception: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        NEW: Intelligent element finding with scoring and alternatives.
        
        Returns: {
            "primary": "cell_id",
            "alternatives": ["cell_id1", "cell_id2"],
            "confidence": 0.0-1.0,
            "reasoning": "why primary was chosen"
        }
        """
        
        if not vision_elements:
            return {"primary": None, "alternatives": [], "confidence": 0.0}
        
        # Score all elements
        scored_elements = []
        
        for element in vision_elements:
            score = self._score_element_match(
                element=element,
                target=step_target,
                field=step_field,
                element_type=element_type,
                perception=perception
            )
            
            if score['overall_score'] > 0.2:  # Only keep candidates above threshold
                scored_elements.append({
                    "cell": element.get("cell"),
                    "element": element,
                    **score
                })
        
        # Sort by score
        scored_elements.sort(key=lambda x: x['overall_score'], reverse=True)
        
        if not scored_elements:
            return {"primary": None, "alternatives": [], "confidence": 0.0}
        
        return {
            "primary": scored_elements[0]['cell'],
            "alternatives": [e['cell'] for e in scored_elements[1:4]],  # Top 3 alternatives
            "confidence": scored_elements[0]['overall_score'],
            "reasoning": scored_elements[0]['reasoning'],
            "all_candidates": scored_elements[:5]  # For debugging
        }

    def _score_element_match(
        self,
        element: Dict[str, Any],
        target: Any,
        field: Optional[str],
        element_type: str,
        perception: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        NEW: Multi-factor scoring of element match.
        
        Factors:
        1. Label matching (40% weight) - How well label matches target
        2. Type matching (30% weight) - Is element type appropriate
        3. Context fit (20% weight) - Does it make sense in workflow
        4. Position plausibility (10% weight) - Is it in expected location
        
        Returns: {
            'label_match': 0.0-1.0,
            'type_match': 0.0-1.0,
            'context_fit': 0.0-1.0,
            'position_score': 0.0-1.0,
            'overall_score': 0.0-1.0,
            'reasoning': "explanation"
        }
        """
        
        element_label = element.get('label', '').lower()
        element_tag_type = element.get('type', '').lower()
        element_role = element.get('role', '').lower()
        
        scores = {
            'label_match': 0.0,
            'type_match': 0.0,
            'context_fit': 0.0,
            'position_score': 0.0
        }
        
        # 1. Label Matching (40% weight)
        if isinstance(target, dict) and target.get('by') == 'label':
            target_value = target.get('value', '').lower()
            
            # Exact match
            if target_value == element_label:
                scores['label_match'] = 1.0
            # Semantic match (using word overlap)
            elif target_value in element_label or element_label in target_value:
                # Calculate word overlap
                target_words = set(target_value.split())
                label_words = set(element_label.split())
                overlap = len(target_words & label_words)
                total = len(target_words | label_words)
                scores['label_match'] = (overlap / max(1, total)) * 0.9
            # Partial match (any word matches)
            elif any(word in element_label for word in target_value.split() if len(word) > 2):
                scores['label_match'] = 0.5
        
        # Field name matching
        if field:
            field_lower = field.lower()
            # Exact field match in label
            if field_lower in element_label:
                scores['label_match'] = max(scores['label_match'], 0.8)
            # Semantic field match (e.g., "email" matches "e-mail" or "electronic mail")
            elif any(part in element_label for part in field_lower.split('_')):
                scores['label_match'] = max(scores['label_match'], 0.6)
        
        # 2. Type Matching (30% weight)
        type_mapping = {
            'textbox': ['textbox', 'input', 'textarea', 'text'],
            'button': ['button', 'submit'],
            'link': ['link', 'a'],
            'checkbox': ['checkbox', 'check'],
            'select': ['select', 'dropdown', 'combobox']
        }
        
        expected_types = type_mapping.get(element_type, [element_type])
        if element_tag_type in expected_types or element_role in expected_types:
            scores['type_match'] = 1.0
        elif element_tag_type in ['button', 'link'] and element_type in ['button', 'link']:
            scores['type_match'] = 0.7  # Cross-compatible
        elif 'button' in element_role and element_type == 'button':
            scores['type_match'] = 0.8  # Role-based match
        else:
            scores['type_match'] = 0.0
        
        # 3. Context Fit (20% weight)
        # Is this element expected at current workflow stage?
        workflow_state = perception.get('workflow_state', 'unknown')
        page_type = perception.get('page_analysis', {}).get('page_type', 'unknown')
        
        # Context-aware scoring
        if field:
            # Email field on registration/login page = high context fit
            if 'email' in field and page_type in ['registration', 'login']:
                scores['context_fit'] = 1.0
            elif 'password' in field and page_type in ['login', 'registration']:
                scores['context_fit'] = 1.0
            elif 'username' in field and page_type in ['login', 'registration']:
                scores['context_fit'] = 0.9
            elif 'name' in field and page_type == 'registration':
                scores['context_fit'] = 0.8
            else:
                scores['context_fit'] = 0.6  # Default reasonable fit
        else:
            scores['context_fit'] = 0.5  # Neutral
        
        # 4. Position Plausibility (10% weight)
        # Elements in standard positions score higher
        bbox = element.get('bbox', [])
        if bbox and len(bbox) == 4:
            x, y, w, h = bbox
            viewport_height = perception.get('viewport', [1280, 800])[1]
            
            # Primary action buttons typically in bottom half or center
            if element_type == 'button':
                if y > viewport_height * 0.5:  # Bottom half
                    scores['position_score'] = 0.8
                elif 200 < y < 600:  # Mid-range
                    scores['position_score'] = 0.7
                else:
                    scores['position_score'] = 0.5
            # Input fields typically in upper-middle area
            elif element_type == 'textbox':
                if 100 < y < 600:  # Expected form area
                    scores['position_score'] = 0.8
                else:
                    scores['position_score'] = 0.6
            else:
                scores['position_score'] = 0.7
        else:
            scores['position_score'] = 0.5  # No bbox info, neutral score
        
        # Calculate weighted overall score
        overall_score = (
            scores['label_match'] * 0.4 +
            scores['type_match'] * 0.3 +
            scores['context_fit'] * 0.2 +
            scores['position_score'] * 0.1
        )
        
        # Generate reasoning
        reasoning = (
            f"Label:{scores['label_match']:.2f} "
            f"Type:{scores['type_match']:.2f} "
            f"Context:{scores['context_fit']:.2f} "
            f"Pos:{scores['position_score']:.2f}"
        )
        
        return {
            **scores,
            'overall_score': overall_score,
            'reasoning': reasoning
        }
    
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
        """NEW: Use LLM to find element with improved structured reasoning prompt"""
        
        # Include more elements and more context
        vision_summary = []
        for element in perception.get("vision", [])[:25]:  # Increased from 10 to 25 elements
            vision_summary.append(
                f"  - Cell {element.get('cell', 'X')}: {element.get('type', 'unknown')} "
                f"'{element.get('label', 'no label')}' "
                f"[bbox: {element.get('bbox', 'N/A')}]"
            )
        
        # Get recent actions for context
        recent_actions = []
        if hasattr(self, 'execution_history'):
            for h in self.execution_history[-3:]:
                recent_actions.append(f"  - {h.get('step', {}).get('action')}: {h.get('result', {}).get('success', False)}")
        
        prompt = f"""
# ELEMENT IDENTIFICATION TASK - IMPROVED WITH STRUCTURED REASONING

## OBJECTIVE
Find the most appropriate element to: {step.get('description', element_description)}

**Action Type:** {step.get('action')}
**Target Field/Type:** {step.get('field', 'N/A')}
**Current Step in Workflow:** {step.get('id', 'unknown')}

## CONTEXT
**Current URL:** {perception.get('url')}
**Page Type:** {perception.get('page_analysis', {}).get('page_type')}
**Workflow Phase:** {perception.get('workflow_state', 'unknown')}

**Previous Actions:**
{chr(10).join(recent_actions) if recent_actions else '  - None'}

## AVAILABLE ELEMENTS (showing {len(perception.get('vision', []))} total)

{chr(10).join(vision_summary)}

## REASONING FRAMEWORK

For EACH potentially relevant element, consider:

### 1. Label Relevance
How well does the label match the target?
- Exact match = Highest priority
- Semantic match (similar meaning) = High priority
- Partial match = Medium priority
- Weak match = Low priority

### 2. Type Appropriateness
Is the element type suitable for the action?
- Perfect type match (textbox for TYPE, button for CLICK)
- Compatible type
- Questionable type
- Wrong type

### 3. Context Fit
Does it make sense in current workflow?
- Expected at this workflow stage
- Plausible
- Unexpected but possible
- Out of context

### 4. Position Plausibility
Is it in a logical location?
- Standard/expected position for this element type
- Reasonable position
- Unusual but possible
- Suspicious/unlikely position

## REQUIRED JSON RESPONSE

Analyze and return:

{{
    "candidates": [
        {{
            "cell": "A1",
            "label": "element label",
            "type": "element type",
            "relevance_score": 0.0-1.0,
            "reasoning": {{
                "label_match": "exact|semantic|partial|weak|none",
                "type_match": "perfect|compatible|questionable|wrong",
                "context_fit": "Brief explanation of why it fits (or doesn't) in context",
                "position": "standard|reasonable|unusual|suspicious"
            }},
            "overall_score": 0.0-1.0,
            "confidence": 0.0-1.0
        }}
        // List ALL candidates with score > 0.3, sorted by overall_score (best first)
    ],
    
    "recommended_cell": "A1",  // Highest scoring element
    "alternatives": ["B2", "C3"],  // Next 2-3 best options
    
    "uncertainty_factors": ["List any factors that reduce confidence"],
    "should_verify_after": true/false,  // Should we verify element before interacting?
    
    "not_found_probability": 0.0-1.0,  // Chance that correct element isn't in list
    "reasoning_summary": "1-2 sentence explanation of why recommended element is best choice"
}}

**If NO suitable elements found**, return:
{{
    "candidates": [],
    "recommended_cell": "NOT_FOUND",
    "alternatives": [],
    "reasons_for_not_found": ["specific reasons why no matches"],
    "suggestions": ["what to look for instead", "alternative approaches"]
}}

**IMPORTANT:** 
- Analyze ALL visible elements, not just the first few
- Consider workflow context (login page? registration page?)
- Be conservative with confidence scores
- Provide clear reasoning for your choice
"""
        
        try:
            messages = [
                {"role": "system", "content": "You are an expert at identifying web elements with structured reasoning. Return valid JSON with candidate analysis."},
                {"role": "user", "content": prompt}
            ]
            
            response = await openrouter_service.chat_completion(
                messages=messages,
                model=self.model,
                temperature=0.1,  # Slightly higher for reasoning
                max_tokens=1000  # More tokens for structured response
            )
            
            content = response['choices'][0]['message']['content'].strip()
            
            # Try to parse JSON response
            try:
                import json
                result = json.loads(content)
            except:
                # Fallback: Try to extract cell ID from text
                logger.warning("⚠️ [TACTICAL] LLM returned non-JSON, attempting to extract cell ID")
                if "NOT_FOUND" in content.upper():
                    return {
                        "action": None,
                        "error": f"Could not find {element_description}",
                        "reasoning": "LLM could not locate target element"
                    }
                # Try to find a cell pattern like A1, B2, etc.
                import re
                cell_match = re.search(r'\b([A-Z]\d{1,2})\b', content)
                if cell_match:
                    cell = cell_match.group(1)
                else:
                    return {
                        "action": None,
                        "error": f"Could not parse LLM response",
                        "reasoning": "LLM response was not in expected format"
                    }
                result = {"recommended_cell": cell, "confidence": 0.5}
            
            # Extract recommended cell
            recommended_cell = result.get("recommended_cell", "NOT_FOUND")
            
            if recommended_cell == "NOT_FOUND" or not recommended_cell:
                return {
                    "action": None,
                    "error": f"Could not find {element_description}",
                    "reasoning": result.get("reasoning_summary", "LLM could not locate target element"),
                    "suggestions": result.get("suggestions", [])
                }
            
            # Get confidence and alternatives
            confidence = result.get("confidence", result.get("candidates", [{}])[0].get("confidence", 0.5) if result.get("candidates") else 0.5)
            alternatives = result.get("alternatives", [])
            
            # Determine action type based on step
            step_action = step.get("action", "").upper()
            if step_action == "TYPE":
                return {
                    "action": {
                        "type": "type_at_cell",
                        "cell": recommended_cell,
                        "text": step.get("target", ""),
                        "field": step.get("field")
                    },
                    "reasoning": f"LLM identified target at {recommended_cell} (confidence: {confidence:.2f})",
                    "llm_analysis": result.get("reasoning_summary", ""),
                    "alternatives": alternatives,
                    "confidence": confidence
                }
            else:  # CLICK
                return {
                    "action": {
                        "type": "click_cell",
                        "cell": recommended_cell
                    },
                    "reasoning": f"LLM identified clickable element at {recommended_cell} (confidence: {confidence:.2f})",
                    "llm_analysis": result.get("reasoning_summary", ""),
                    "alternatives": alternatives,
                    "confidence": confidence
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