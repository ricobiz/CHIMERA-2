import os
import base64
from typing import Dict, Any, List
import httpx
import json

# Supervisor (Step Brain) via OpenRouter (text-first, robust JSON)
# Default model can be overridden by request payload or env
DEFAULT_VLM = os.environ.get('AUTOMATION_VLM_MODEL', 'openai/gpt-4o-mini')

SYSTEM_PROMPT = (
    "You are a step supervisor for browser automation. "
    "Decide the next single action strictly as JSON. "
    "Do not include any prose. Return only a single JSON object with the fields in the schema."
)

JSON_SCHEMA_EXAMPLE = {
    "next_action": "CLICK_CELL | TYPE_AT_CELL | HOLD_DRAG | SCROLL | WAIT | DONE | ERROR",
    "target_cell": "C7",
    "text": "optional for TYPE_AT_CELL",
    "direction": "up|down (for SCROLL)",
    "amount": 400,
    "needs_user_input": False,
    "ask_user": "",
    "confidence": 0.5,
}

SAFE_MODELS = [
    lambda: os.environ.get('AUTOMATION_VLM_MODEL'),
    lambda: 'openai/gpt-4o-mini',
    lambda: 'anthropic/claude-3.5-sonnet',
    lambda: 'qwen/qwen2.5',
]

class SupervisorService:
    def _extract_json(self, content: str) -> Dict[str, Any]:
        """Best-effort JSON extraction from model text."""
        try:
            return json.loads(content)
        except Exception:
            pass
        # Try to find the first JSON object
        start = content.find('{')
        end = content.rfind('}')
        if start != -1 and end != -1 and end > start:
            snippet = content[start:end+1]
            try:
                return json.loads(snippet)
            except Exception:
                pass
        return {"error": "Non-JSON content", "raw": content[:400]}

    async def _call_openrouter(self, messages: List[Dict[str, str]], model: str) -> Dict[str, Any]:
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            return {"error": "OpenRouter API key not configured"}

        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": os.environ.get("OPENROUTER_HTTP_REFERER", "https://lovable.studio"),
            "X-Title": os.environ.get("OPENROUTER_X_TITLE", "Lovable Studio"),
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 400
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            if resp.status_code != 200:
                return {"error": f"OpenRouter error {resp.status_code}", "details": resp.text[:500]}
            data = resp.json()
            try:
                content = data['choices'][0]['message']['content']
            except Exception:
                return {"error": "Malformed OpenRouter response", "raw": data}
            return self._extract_json(content)

    async def next_step(self, goal: str, history: List[Dict[str, Any]], screenshot_base64: str,
                        vision: List[Dict[str, Any]], model: str = DEFAULT_VLM) -> Dict[str, Any]:
        # Build the prompt (compact)
        user_parts = [
            f"GOAL: {goal}",
            "You receive fresh screenshot description and vision elements (cell/label/type/confidence).",
            "Decide ONE next action using the provided grid cells.",
            "Return STRICT JSON ONLY using this schema keys: next_action, target_cell, text, direction, amount, needs_user_input, ask_user, confidence."
        ]
        # include a compact list of vision elements (cap at 40)
        lines = []
        for el in (vision or [])[:40]:
            lines.append(f"- {el.get('type')} '{el.get('label')}' @ {el.get('cell')} conf={el.get('confidence')}")
        user_parts.append("VISION:\n" + "\n".join(lines))
        user_prompt = "\n\n".join(user_parts)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        # Try selected model and then safe fallbacks on 400/404/other errors
        tried_errors = []
        for getter in SAFE_MODELS:
            m = None
            try:
                m = getter()
            except Exception:
                m = None
            if not m:
                continue
            result = await self._call_openrouter(messages, m)
            if not result.get('error'):
                return result
            tried_errors.append({"model": m, "error": result.get('error'), "details": result.get('details')})
        # If none succeeded, return the last error with context
        return {"error": "Brain request failed", "tried": tried_errors}

supervisor_service = SupervisorService()
