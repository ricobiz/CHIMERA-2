import os
import base64
from typing import Dict, Any, List
import httpx

# Supervisor (Step Brain) via OpenRouter VLM
# Default model can be overridden by request payload
DEFAULT_VLM = os.environ.get('AUTOMATION_VLM_MODEL', 'qwen/qwen2.5-vl')

SYSTEM_PROMPT = (
    "You are a step supervisor for browser automation. "
    "Decide the next single action strictly as JSON. "
    "Never include extra text. Always return fields as specified."
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
    "then": { "next_action": "CLICK_CELL", "target_cell": "D4" }
}

class SupervisorService:
    async def next_step(self, goal: str, history: List[Dict[str, Any]], screenshot_base64: str,
                        vision: List[Dict[str, Any]], model: str = DEFAULT_VLM) -> Dict[str, Any]:
        # Build the prompt
        user_parts = [
            f"GOAL: {goal}",
            "You receive fresh screenshot (base64 truncated) and vision elements (cell/label/type/confidence).",
            "Return STRICT JSON ONLY. Use the grid cells."
        ]
        # include a compact list of vision elements
        lines = []
        for el in vision[:60]:
            lines.append(f"- {el.get('type')} '{el.get('label')}' @ {el.get('cell')} conf={el.get('confidence')}")
        user_parts.append("VISION:\n" + "\n".join(lines))
        user_prompt = "\n\n".join(user_parts) + "\n\nJSON ONLY: " + str(JSON_SCHEMA_EXAMPLE)

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
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"}
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
            # Ensure JSON
            try:
                import json
                parsed = json.loads(content)
                return parsed
            except Exception:
                return {"error": "Non-JSON content", "raw": content[:400]}

supervisor_service = SupervisorService()
