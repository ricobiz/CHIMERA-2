"""
AntiBot Guard - Enhanced detection and policy
Extends basic antibot from scene_builder_service
"""
import logging
import json
from typing import Dict, Any, List, Optional
from playwright.async_api import Page
from services.openrouter_service import openrouter_service

logger = logging.getLogger(__name__)

class AntiBotGuard:
    """
    Enhanced antibot detection and policy engine
    """
    
    def __init__(self):
        self.model = "qwen/qwen3-coder-flash"
        self.max_retries = 2
        self.backoff_ms = 4000
        
        # Available profiles
        self.profiles = {
            "default": {"name": "default", "type": "standard"},
            "stealth": {"name": "stealth", "type": "enhanced"},
            "slow_proxy": {"name": "slow_proxy", "type": "residential"},
            "alt_ua": {"name": "alt_ua", "type": "alternate_ua"},
            "alt_tz": {"name": "alt_tz", "type": "alternate_timezone"}
        }
    
    async def eval_policy(
        self,
        scene: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate antibot policy
        Returns: {decision: {action, profile?, backoff_ms}}
        """
        try:
            antibot = scene.get('antibot', {})
            
            if not antibot.get('present'):
                return {
                    "decision": {
                        "action": "continue",
                        "profile": None,
                        "backoff_ms": 0
                    }
                }
            
            # Count previous antibot encounters
            antibot_count = sum(1 for h in history if h.get('antibot_encountered', False))
            
            antibot_type = antibot.get('type', 'unknown')
            severity = antibot.get('severity', 0.5)
            
            # Policy decisions
            if antibot_type == 'captcha':
                provider = antibot.get('provider', '')
                # Support recaptcha (v2/v3), hcaptcha, turnstile
                if any(p in provider.lower() for p in ['recaptcha', 'hcaptcha', 'turnstile']):
                    return {
                        "decision": {
                            "action": "wait_solver",
                            "profile": None,
                            "backoff_ms": 0,
                            "message": f"CAPTCHA detected: {provider}"
                        }
                    }
                else:
                    return {
                        "decision": {
                            "action": "abort",
                            "profile": None,
                            "backoff_ms": 0,
                            "reason": f"Unsupported captcha type: {provider}"
                        }
                    }
            
            elif antibot_type == 'rate_limit':
                if antibot_count < self.max_retries:
                    return {
                        "decision": {
                            "action": "backoff",
                            "profile": "slow_proxy",
                            "backoff_ms": self.backoff_ms * (antibot_count + 1)
                        }
                    }
                else:
                    return {
                        "decision": {
                            "action": "abort",
                            "profile": None,
                            "backoff_ms": 0,
                            "reason": "Max retries exceeded"
                        }
                    }
            
            elif 'cf' in antibot_type or antibot_type == 'interstitial':
                if antibot_count == 0:
                    return {
                        "decision": {
                            "action": "switch_profile",
                            "profile": "stealth",
                            "backoff_ms": self.backoff_ms
                        }
                    }
                elif antibot_count < self.max_retries:
                    return {
                        "decision": {
                            "action": "backoff",
                            "profile": "slow_proxy",
                            "backoff_ms": self.backoff_ms * 2
                        }
                    }
                else:
                    return {
                        "decision": {
                            "action": "abort",
                            "profile": None,
                            "backoff_ms": 0,
                            "reason": "CF challenge failed multiple times"
                        }
                    }
            
            elif antibot_type == 'login_wall':
                return {
                    "decision": {
                        "action": "consent_click",
                        "profile": None,
                        "backoff_ms": 0
                    }
                }
            
            else:
                # Unknown antibot type - try retry once
                if antibot_count < 1:
                    return {
                        "decision": {
                            "action": "retry",
                            "profile": None,
                            "backoff_ms": self.backoff_ms
                        }
                    }
                else:
                    return {
                        "decision": {
                            "action": "abort",
                            "profile": None,
                            "backoff_ms": 0,
                            "reason": "Unknown antibot type"
                        }
                    }
            
        except Exception as e:
            logger.error(f"AntiBot policy eval error: {e}")
            return {
                "decision": {
                    "action": "abort",
                    "profile": None,
                    "backoff_ms": 0,
                    "reason": f"Policy error: {e}"
                }
            }
    
    async def switch_profile(
        self,
        browser_service,
        session_id: str,
        profile_name: str
    ) -> Dict[str, Any]:
        """
        Switch to different browser profile
        """
        try:
            profile = self.profiles.get(profile_name)
            if not profile:
                return {"ok": False, "error": f"Profile {profile_name} not found"}
            
            # In real implementation: recreate session with new profile
            logger.info(f"Switching to profile: {profile_name}")
            
            # For now: return success
            return {
                "ok": True,
                "profile": profile_name,
                "message": f"Switched to {profile_name} profile"
            }
            
        except Exception as e:
            logger.error(f"Profile switch error: {e}")
            return {"ok": False, "error": str(e)}
    
    def get_available_profiles(self) -> List[Dict[str, Any]]:
        """Get list of available profiles"""
        return list(self.profiles.values())


# Global instance
antibot_guard = AntiBotGuard()
