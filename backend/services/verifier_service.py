"""
Verifier & Recovery Services
Compare scenes, generate remediation, plan recovery
"""
import logging
import json
from typing import Dict, Any, List, Optional
from services.openrouter_service import openrouter_service

logger = logging.getLogger(__name__)

class VerifierService:
    """
    Verifier: Compare prev/curr scenes and verify action effects
    """
    
    def __init__(self):
        self.model = "qwen/qwen3-coder-flash"
        self.temperature = 0.0
    
    async def verify(
        self,
        prev_scene: Dict[str, Any],
        curr_scene: Dict[str, Any],
        last_action: Dict[str, Any],
        goal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Verify if action had expected effect
        Returns: {success, reason, remediation}
        """
        try:
            # Quick checks first
            prev_url = prev_scene.get('url', '')
            curr_url = curr_scene.get('url', '')
            action_type = last_action.get('action', '')
            
            # URL change expectations
            if action_type == 'navigate':
                expected_url = last_action.get('url', '')
                if expected_url and expected_url not in curr_url:
                    return {
                        "success": False,
                        "expected": f"URL contains {expected_url}",
                        "observed": f"URL is {curr_url}",
                        "remediation": "retry_target"
                    }
            
            # Element state changes
            prev_elements = {el['id']: el for el in prev_scene.get('elements', [])}
            curr_elements = {el['id']: el for el in curr_scene.get('elements', [])}
            
            # Check for new elements (dialog, form, etc.)
            new_elements = len(curr_elements) - len(prev_elements)
            
            # Check for antibot changes
            prev_antibot = prev_scene.get('antibot', {}).get('present', False)
            curr_antibot = curr_scene.get('antibot', {}).get('present', False)
            
            if not prev_antibot and curr_antibot:
                return {
                    "success": False,
                    "expected": "No antibot trigger",
                    "observed": "Antibot appeared",
                    "remediation": "switch_profile"
                }
            
            # Check for loading state
            if curr_scene.get('hints', {}).get('loading', False):
                return {
                    "success": False,
                    "expected": "Page loaded",
                    "observed": "Still loading",
                    "remediation": "wait"
                }
            
            # Check for dialogs (might need close)
            dialog_count = curr_scene.get('hints', {}).get('dialogs', 0)
            if dialog_count > 0:
                return {
                    "success": True,
                    "expected": "Action completed",
                    "observed": f"Dialog appeared ({dialog_count})",
                    "remediation": "close_dialog"
                }
            
            # Default: assume success if no issues
            return {
                "success": True,
                "expected": f"Action {action_type} completed",
                "observed": "Scene changed appropriately",
                "remediation": "none"
            }
            
        except Exception as e:
            logger.error(f"Verify error: {e}")
            return {
                "success": False,
                "expected": "Verification",
                "observed": f"Error: {e}",
                "remediation": "abort"
            }


class RecoveryService:
    """
    Recovery: Generate recovery steps from remediation hint
    """
    
    def __init__(self):
        self.model = "qwen/qwen3-coder-flash"
        self.temperature = 0.1
    
    async def plan_recovery(
        self,
        scene: Dict[str, Any],
        remediation: str,
        goal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate recovery steps
        Returns: {steps: [Action]}
        """
        try:
            recovery_map = {
                "retry_target": self._retry_action,
                "scroll": self._scroll_recovery,
                "close_dialog": self._close_dialog,
                "switch_tab": self._switch_tab,
                "wait": self._wait_recovery,
                "vlm_ground": self._vlm_ground,
                "switch_profile": self._switch_profile,
                "abort": self._abort
            }
            
            recovery_fn = recovery_map.get(remediation, self._default_recovery)
            steps = await recovery_fn(scene, goal)
            
            return {
                "success": True,
                "steps": steps
            }
            
        except Exception as e:
            logger.error(f"Recovery planning error: {e}")
            return {
                "success": False,
                "steps": [],
                "error": str(e)
            }
    
    async def _retry_action(self, scene: Dict[str, Any], goal: Dict[str, Any]) -> List[Dict]:
        """Retry last action"""
        return [
            {"action": "wait", "ms": 1000, "explain": "wait before retry"},
            {"action": "retry_last", "explain": "retry previous action"}
        ]
    
    async def _scroll_recovery(self, scene: Dict[str, Any], goal: Dict[str, Any]) -> List[Dict]:
        """Scroll to find element"""
        return [
            {"action": "scroll", "dy": 400, "explain": "scroll down to find element"}
        ]
    
    async def _close_dialog(self, scene: Dict[str, Any], goal: Dict[str, Any]) -> List[Dict]:
        """Close dialog"""
        return [
            {"action": "key_press", "key": "Escape", "explain": "close dialog"},
            {"action": "wait", "ms": 500, "explain": "wait for dialog close"}
        ]
    
    async def _switch_tab(self, scene: Dict[str, Any], goal: Dict[str, Any]) -> List[Dict]:
        """Switch tab"""
        return [
            {"action": "switch_tab", "index": 0, "explain": "switch to main tab"}
        ]
    
    async def _wait_recovery(self, scene: Dict[str, Any], goal: Dict[str, Any]) -> List[Dict]:
        """Wait for loading"""
        return [
            {"action": "wait", "ms": 2000, "explain": "wait for page load"}
        ]
    
    async def _vlm_ground(self, scene: Dict[str, Any], goal: Dict[str, Any]) -> List[Dict]:
        """Use VLM for grounding"""
        return [
            {"action": "vlm_detect", "description": "target element", "explain": "use vision to find element"}
        ]
    
    async def _switch_profile(self, scene: Dict[str, Any], goal: Dict[str, Any]) -> List[Dict]:
        """Switch profile on antibot"""
        return [
            {"action": "abort", "reason": "antibot_detected", "explain": "antibot requires profile switch"}
        ]
    
    async def _abort(self, scene: Dict[str, Any], goal: Dict[str, Any]) -> List[Dict]:
        """Abort execution"""
        return [
            {"action": "abort", "reason": "unrecoverable_error", "explain": "cannot proceed"}
        ]
    
    async def _default_recovery(self, scene: Dict[str, Any], goal: Dict[str, Any]) -> List[Dict]:
        """Default recovery"""
        return [
            {"action": "wait", "ms": 1000, "explain": "default recovery wait"}
        ]


# Global instances
verifier_service = VerifierService()
recovery_service = RecoveryService()
