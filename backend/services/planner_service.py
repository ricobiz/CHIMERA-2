"""
Planner Service (UIG) - Multi-path planning with A/B/C candidates
Uses Qwen2.5-Instruct via OpenRouter
"""
import logging
import json
from typing import Dict, Any, List, Optional
from services.openrouter_service import openrouter_service

logger = logging.getLogger(__name__)

class PlannerService:
    """
    UIG Planner: Generates multi-path plans (A/B/C) from goal + Scene
    Model: Qwen2.5-Instruct (or fallback)
    """
    
    def __init__(self):
        self.model = "qwen/qwen-2.5-instruct"  # OpenRouter model ID
        self.temperature = 0.10
        self.top_p = 0.85
    
    async def decide_plan(
        self,
        goal: Dict[str, Any],
        scene: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate multi-path plan from goal + scene
        
        Returns Plan JSON:
        {
          "goal": {"site": "...", "task": "register|login|..."},
          "context": {"http": 200, "antibot": {...}},
          "assumptions": ["..."],
          "risks": ["..."],
          "candidates": [
            {
              "id": "A",
              "why": "reason",
              "pre": {"elements": ["button:Sign up"]},
              "steps": [{action, target, ...}],
              "success": {"url_includes": [...]},
              "stop_on": [...]
            }
          ],
          "chosen": "A"
        }
        """
        try:
            # Build prompt
            prompt = self._build_planner_prompt(goal, scene, context)
            
            # Call LLM
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ]
            
            response = await openrouter_service.chat_completion(
                messages=messages,
                model=self.model,
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=4000
            )
            
            content = response['choices'][0]['message']['content']
            
            # Parse JSON
            plan = self._parse_plan_json(content)
            
            logger.info(f"📋 Plan generated: {len(plan.get('candidates', []))} candidates, chosen={plan.get('chosen')}")
            
            return {
                "success": True,
                "plan": plan,
                "usage": response.get('usage', {})
            }
            
        except Exception as e:
            logger.error(f"Planning error: {e}")
            return {
                "success": False,
                "error": str(e),
                "plan": self._get_fallback_plan(goal)
            }
    
    def _get_system_prompt(self) -> str:
        """System prompt for planner"""
        return """You are the Planner (UIG) for HIMERA Automation.

Build 1-3 candidate plans (A/B/C) with preconditions, concrete steps, success signals, and stop conditions.

RULES:
1. Plans MUST reference ONLY elements present in Scene (role/label/id)
2. Add bbox fallback when available
3. If required element missing, prefer alternate plan
4. NEVER click captcha; stop on anti-bot
5. Keep each candidate ≤6 steps
6. Return ONLY valid JSON, no markdown

Output format:
{
  "goal": {"site": "...", "task": "register|login|navigate|fill_form"},
  "context": {"http": 200, "antibot": {"present": false}},
  "assumptions": ["..."],
  "risks": ["..."],
  "candidates": [
    {
      "id": "A",
      "why": "reason",
      "pre": {"elements": ["button:Sign up|Create account"]},
      "steps": [
        {
          "action": "click",
          "target": {"by": "label", "value": "Sign up"},
          "fallback": {"by": "bbox", "value": [100, 200, 300, 240]},
          "explain": "click signup"
        }
      ],
      "success": {"url_includes": ["/welcome", "/verify"]},
      "stop_on": ["antibot.present", "dialog:error"]
    }
  ],
  "chosen": "A"
}"""
    
    def _build_planner_prompt(
        self,
        goal: Dict[str, Any],
        scene: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build planning prompt"""
        # Extract key info from scene
        elements_summary = self._summarize_elements(scene.get('elements', []))
        antibot = scene.get('antibot', {})
        url = scene.get('url', '')
        
        prompt = f"""Plan automation for this goal:

GOAL:
Site: {goal.get('site', url)}
Task: {goal.get('task', 'unknown')}

CURRENT SCENE:
URL: {url}
Viewport: {scene.get('viewport', [1280, 800])}
Anti-bot: {antibot.get('present', False)} ({antibot.get('type', 'none')})
HTTP: {scene.get('http', {}).get('status', 200)}

AVAILABLE ELEMENTS ({len(scene.get('elements', []))}):
{elements_summary}

HINTS:
Language: {scene.get('hints', {}).get('lang', 'en')}
Dialogs: {scene.get('hints', {}).get('dialogs', 0)}
Captcha: {scene.get('hints', {}).get('captcha', False)}

Generate 1-3 candidate plans. Consider:
- Elements visibility and availability
- Anti-bot status
- Most efficient path
- Fallback options

Return ONLY JSON (no markdown):"""
        
        return prompt
    
    def _summarize_elements(self, elements: List[Dict[str, Any]]) -> str:
        """Summarize elements for prompt"""
        if not elements:
            return "No interactive elements found"
        
        # Group by role
        by_role = {}
        for el in elements[:30]:  # Limit to 30 for prompt size
            role = el.get('role', 'element')
            label = el.get('label', '')[:40]
            if label:
                by_role.setdefault(role, []).append(label)
        
        summary = []
        for role, labels in by_role.items():
            summary.append(f"- {role}: {', '.join(labels[:5])}")
        
        return '\n'.join(summary[:15])
    
    def _parse_plan_json(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        # Remove markdown code blocks if present
        content = content.strip()
        if content.startswith('```'):
            lines = content.split('\n')
            content = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])
        
        content = content.replace('```json', '').replace('```', '').strip()
        
        try:
            plan = json.loads(content)
            
            # Validate structure
            if 'candidates' not in plan:
                plan['candidates'] = []
            if 'chosen' not in plan and plan['candidates']:
                plan['chosen'] = plan['candidates'][0]['id']
            if 'assumptions' not in plan:
                plan['assumptions'] = []
            if 'risks' not in plan:
                plan['risks'] = []
            
            return plan
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}\nContent: {content[:500]}")
            raise ValueError(f"Invalid JSON from planner: {e}")
    
    def _get_fallback_plan(self, goal: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback plan on error"""
        return {
            "goal": goal,
            "context": {"http": 200, "antibot": {"present": False}},
            "assumptions": ["Fallback plan - planner error"],
            "risks": ["No proper plan generated"],
            "candidates": [
                {
                    "id": "A",
                    "why": "Fallback - wait and retry",
                    "pre": {},
                    "steps": [{"action": "wait", "ms": 1000, "explain": "wait before retry"}],
                    "success": {},
                    "stop_on": []
                }
            ],
            "chosen": "A"
        }

# Global instance
planner_service = PlannerService()
