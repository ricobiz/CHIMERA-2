"""
Cognitive Loop Services - Awareness, EnvCheck, Recon, Inventory
Implements cognitive stages from Technical Assignment
"""
import logging
import json
from typing import Dict, Any, List, Optional
from services.openrouter_service import openrouter_service

logger = logging.getLogger(__name__)

class AwarenessService:
    """Awareness: Normalize goal and propose routes"""
    
    def __init__(self):
        self.model = "openai/gpt-5"  # Use GPT-5 for awareness
        self.temperature = 0.12
    
    async def think(
        self,
        raw_goal: str,
        site: str,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Normalize goal and propose routes"""
        try:
            prompt = f"""Analyze this automation goal:

RAW GOAL: {raw_goal}
SITE: {site}
CONSTRAINTS: {json.dumps(constraints or {})}

Output JSON only (no markdown):
{{
  "goal": {{"site": "...", "task": "register|login|fill_form|navigate|other"}},
  "routes": [
    {{"id": "A", "idea": "...", "assumptions": ["..."]}}
  ],
  "risks": ["..."],
  "unknowns": ["..."]
}}"""
            
            messages = [{"role": "user", "content": prompt}]
            response = await openrouter_service.chat_completion(
                messages=messages,
                model=self.model,
                temperature=self.temperature,
                max_tokens=1000
            )
            
            content = response['choices'][0]['message']['content']
            result = self._parse_json(content)
            
            return {"success": True, "result": result}
            
        except Exception as e:
            logger.error(f"Awareness error: {e}")
            return {"success": False, "error": str(e)}
    
    def _parse_json(self, content: str) -> Dict:
        content = content.strip().replace('```json', '').replace('```', '').strip()
        return json.loads(content)


class EnvCheckService:
    """Environment Check: Classify current state"""
    
    def __init__(self):
        self.model = "qwen/qwen3-coder-flash"
        self.temperature = 0.0
    
    async def check(
        self,
        session_id: str,
        url: str,
        http_status: int,
        antibot: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check environment status"""
        try:
            needs_attention = []
            page_status = "ok"
            
            if http_status >= 400:
                page_status = "error"
                needs_attention.append("http_error")
            elif http_status == 429:
                page_status = "blocked"
                needs_attention.append("rate_limit")
            
            if antibot.get('present'):
                if antibot.get('type') == 'captcha':
                    page_status = "captcha"
                    needs_attention.append("anti_bot_eval")
                elif 'cf' in antibot.get('type', ''):
                    page_status = "interstitial"
                    needs_attention.append("profile_switch")
            
            message = "Environment OK" if page_status == "ok" else f"Issue: {page_status}"
            
            return {
                "net": "ok",
                "browser": "ok",
                "page": page_status,
                "http": http_status,
                "needs_attention": needs_attention,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"EnvCheck error: {e}")
            return {
                "net": "ok",
                "browser": "ok",
                "page": "error",
                "http": 500,
                "needs_attention": ["retry_later"],
                "message": str(e)
            }


class ReconService:
    """Recon: Identify entry points"""
    
    def __init__(self):
        self.model = "qwen/qwen3-coder-flash"
        self.temperature = 0.0
    
    async def scan(
        self,
        scene: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Scan for entry points"""
        try:
            elements = scene.get('elements', [])
            entry_points = []
            
            # Look for common entry patterns
            patterns = [
                ('sign up', 'button|link'),
                ('register', 'button|link'),
                ('create account', 'button|link'),
                ('login', 'button|link'),
                ('sign in', 'button|link'),
                ('search', 'textbox')
            ]
            
            for el in elements:
                label = el.get('label', '').lower()
                role = el.get('role', '')
                
                for pattern, expected_role in patterns:
                    if pattern in label and (expected_role == 'button|link' or role in expected_role):
                        entry_points.append(f"{role}:{el.get('label', '')}")
            
            antibot = scene.get('antibot', {})
            blocked = antibot.get('present', False)
            captcha = antibot.get('type') == 'captcha'
            
            notes = f"Found {len(entry_points)} entry points" if entry_points else "No obvious entry points"
            if blocked:
                notes += "; antibot detected"
            
            return {
                "entry_points": entry_points[:10],
                "blocked": blocked,
                "captcha": captcha,
                "notes": notes
            }
            
        except Exception as e:
            logger.error(f"Recon error: {e}")
            return {
                "entry_points": [],
                "blocked": False,
                "captcha": False,
                "notes": f"Scan error: {e}"
            }


class InventoryService:
    """Inventory Gate: Check resource availability"""
    
    def __init__(self):
        self.model = "qwen/qwen3-coder-flash"
        self.temperature = 0.0
    
    async def check(
        self,
        goal: Dict[str, Any],
        plan: Dict[str, Any],
        available_resources: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Check if resources available for execution"""
        try:
            resources = available_resources or {}
            task = goal.get('task', '')
            
            # Default needs for each task
            needs_map = {
                'register': ['email_inbox', 'username_gen', 'password_gen'],
                'login': ['username_gen', 'password_gen'],
                'fill_form': ['username_gen'],
                'navigate': []
            }
            
            needs = needs_map.get(task, [])
            gaps = []
            advice = []
            blockers = []
            
            for need in needs:
                if not resources.get(need):
                    gaps.append(need)
                    if need == 'email_inbox':
                        blockers.append(f"missing {need}")
                    else:
                        advice.append(f"Generate {need.replace('_gen', '')} before execution")
            
            # Check proxy if antibot present
            plan_context = plan.get('context', {})
            if plan_context.get('antibot', {}).get('present'):
                if not resources.get('proxy_profile'):
                    advice.append("Consider using proxy profile for antibot")
            
            go = len(blockers) == 0
            
            return {
                "go": go,
                "gaps": gaps,
                "advice": advice,
                "blockers": blockers
            }
            
        except Exception as e:
            logger.error(f"Inventory check error: {e}")
            return {
                "go": False,
                "gaps": [],
                "advice": [],
                "blockers": [f"Inventory error: {e}"]
            }


# Global instances
awareness_service = AwarenessService()
env_check_service = EnvCheckService()
recon_service = ReconService()
inventory_service = InventoryService()
