import os
import base64
from typing import Dict, Any, List
import httpx
import json
import re

# Supervisor (Step Brain) via OpenRouter (text-first, robust JSON)
# Default model can be overridden by request payload or env
DEFAULT_VLM = os.environ.get('AUTOMATION_VLM_MODEL', 'openai/gpt-4o-mini')

SYSTEM_PROMPT = (
    "You are a step supervisor for browser automation. "
    "Decide the next single action strictly as JSON. "
    "Do not include any prose. Return only a single JSON object with the fields in the schema. "
    "\n\nIMPORTANT RULES:\n"
    "- If you see interactive elements (buttons, links, inputs) - ACT on them, don't just WAIT\n"
    "- WAIT should only be used if page is loading or you need time between actions\n"
    "- If no elements visible - try SCROLL to find them\n"
    "- If goal requires navigation and current page doesn't match - use NAVIGATE\n"
    "- Avoid repeating WAIT more than 2 times in a row"
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

CELL_RE = re.compile(r"^[A-Z][0-9]{1,2}$")

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

    def _map_label_to_cell(self, label: str, vision: List[Dict[str, Any]]) -> str:
        """Find cell in vision by fuzzy label match."""
        if not label:
            return ''
        L = label.lower()
        best = None
        for el in vision or []:
            lab = (el.get('label') or '').lower()
            if L in lab or lab in L:
                if not best or float(el.get('confidence', 0.0)) > float(best.get('confidence', 0.0)):
                    best = el
        return best.get('cell') if best else ''

    def _normalize(self, raw: Dict[str, Any], vision: List[Dict[str, Any]]) -> Dict[str, Any]:
        if raw.get('error'):
            return raw
        action = (raw.get('next_action') or raw.get('action') or '').upper().strip()
        # Normalize action aliases
        if action in ('CLICK', 'PRESS'):
            action = 'CLICK_CELL'
        if action in ('TYPE', 'INPUT'):
            action = 'TYPE_AT_CELL'
        if action in ('DRAG', 'DRAG_DROP'):
            action = 'HOLD_DRAG'
        if action not in ('CLICK_CELL', 'TYPE_AT_CELL', 'HOLD_DRAG', 'SCROLL', 'WAIT', 'DONE'):
            # fallback to WAIT to avoid infinite warnings
            return {"next_action": "WAIT", "amount": 400}

        target_cell = raw.get('target_cell') or raw.get('cell') or ''
        if target_cell and not CELL_RE.match(str(target_cell).upper()):
            # try map label -> cell
            mapped = self._map_label_to_cell(str(target_cell), vision)
            if mapped:
                target_cell = mapped
            else:
                target_cell = ''
        elif target_cell:
            target_cell = str(target_cell).upper()

        out = {
            "next_action": action,
            "target_cell": target_cell,
            "text": raw.get('text') or '',
            "direction": raw.get('direction', 'down'),
            "amount": int(raw.get('amount', 400) or 400),
            "needs_user_input": bool(raw.get('needs_user_input', False)),
            "ask_user": raw.get('ask_user', ''),
            "confidence": float(raw.get('confidence', 0.5))
        }
        # Bound amount
        out['amount'] = max(100, min(800, out['amount']))
        return out

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

        tried_errors = []
        for getter in SAFE_MODELS:
            m = None
            try:
                m = getter()
            except Exception:
                m = None
            if not m:
                continue
            raw = await self._call_openrouter(messages, m)
            if not raw.get('error'):
                return self._normalize(raw, vision)
            tried_errors.append({"model": m, "error": raw.get('error'), "details": raw.get('details')})
        return {"error": "Brain request failed", "tried": tried_errors}

supervisor_service = SupervisorService()
