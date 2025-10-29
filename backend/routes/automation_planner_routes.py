from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
import os
import json
import random
import logging
from datetime import datetime

from services.profile_service import PROFILES_DIR
from services.profile_service import profile_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/automation/plan", tags=["automation-planner"])

class AnalyzeRequest(BaseModel):
    goal: str

class GenerateRequest(BaseModel):
    task_id: str
    analysis: Dict[str, Any]

# Utilities

def _find_warm_profile() -> Optional[Dict[str, Any]]:
    try:
        if not os.path.exists(PROFILES_DIR):
            return None
        for pid in os.listdir(PROFILES_DIR):
            meta_path = os.path.join(PROFILES_DIR, pid, 'meta.json')
            if os.path.exists(meta_path):
                with open(meta_path, 'r') as f:
                    meta = json.load(f)
                warm = meta.get('warmup', {}).get('is_warm') or meta.get('status') in ('warm', 'active')
                proxy_type = (meta.get('proxy', {}) or {}).get('proxy_type')
                if warm and proxy_type and proxy_type != 'datacenter':
                    meta['profile_id'] = pid
                    return meta
    except Exception as e:
        logger.warning(f"find_warm_profile error: {e}")
    return None

@router.post('/analyze')
async def analyze(req: AnalyzeRequest):
    try:
        goal_norm = (req.goal or '').strip().lower()
        task_id = str(uuid.uuid4())

        # Understand task (basic intent classification)
        understood = "Register new Gmail account with email/password credentials" if 'gmail' in goal_norm else req.goal

        # Requirements
        requirements = {
            "mandatory": ["first_name","last_name","username","password","birthday"],
            "optional": ["phone_number","recovery_email"],
            "probable_challenges": [
                {"type": "captcha_checkbox", "probability": 0.8},
                {"type": "captcha_image_selection", "probability": 0.4},
                {"type": "phone_verification", "probability": 0.6},
                {"type": "page_change_detection", "probability": 1.0},
                {"type": "visual_confirmation", "probability": 1.0}
            ],
            "technical": ["warm_profile","residential_proxy","human_behavior","captcha_solver"]
        }

        # Availability
        warm_meta = _find_warm_profile()
        availability = {
            "profile": {
                "status": "available" if warm_meta else "unavailable",
                "profile_id": warm_meta.get('profile_id') if warm_meta else None,
                "is_warm": bool(warm_meta and (warm_meta.get('warmup',{}).get('is_warm') or warm_meta.get('status') in ('warm','active'))),
                "proxy_type": (warm_meta.get('proxy',{}) or {}).get('proxy_type') if warm_meta else None
            },
            "notes": "No warm profile found; you may proceed without warmup for non-strict sites or run warmup now.",
            "can_proceed_without_warm": True
        }

        # Risk assessment
        can_start = True  # allow starting even if no warm profile
        base_prob = 0.75 if (warm_meta and availability['profile']['proxy_type'] != 'datacenter') else 0.5
        # If no warm profile, reduce probability slightly
        if not warm_meta:
            base_prob -= 0.15
        success_probability = base_prob
        decision = {
            "can_proceed": can_start,
            "strategy": "attempt_without_phone_fallback_to_user",
            "success_probability": round(max(0.0, min(0.99, success_probability)), 2),
            "expected_waiting_user": True,
            "expected_waiting_reason": "phone_verification",
            "reason": "Warm profile recommended but not required for this goal. Proceed with caution."
        }

        return {
            "task_id": task_id,
            "goal": req.goal,
            "analysis": {
                "understood_task": understood,
                "requirements": {
                    "mandatory_data": requirements['mandatory'],
                    "optional_data": requirements['optional'],
                    "probable_challenges": [
                        {"type": "captcha", "probability": 0.8, "solvable": True},
                        {"type": "phone_verification", "probability": 0.6, "solvable": False}
                    ]
                },
                "availability": {
                    **availability,
                },
                "decision": decision
            },
            "next_step": "generate_plan"
        }
    except Exception as e:
        logger.error(f"Analyze error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Data generation and /generate unchanged (omitted for brevity in this diff) but still present

FIRST_NAMES = ["Ivan","Alex","John","Peter","Michael","Ethan","Liam","Noah","Mason","James"]
LAST_NAMES  = ["Petrov","Smirnov","Johnson","Miller","Brown","Davis","Wilson","Moore","Taylor","Anderson"]


def _gen_username(fn: str, ln: str) -> str:
    suffix = random.randint(1000, 9999)
    base = f"{fn}.{ln}".lower()
    return f"{base}.{suffix}"


def _gen_password() -> str:
    letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    digits = '0123456789'
    symbols = '!@#$%^&*'
    pw = [random.choice(letters) for _ in range(6)] + [random.choice(digits) for _ in range(3)] + [random.choice(symbols)]
    random.shuffle(pw)
    return ''.join(pw)


def _gen_birthday() -> str:
    year = random.randint(1985, 2003)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{year:04d}-{month:02d}-{day:02d}"

@router.post('/generate')
async def generate(req):
    try:
        analysis = req.analysis or {}
        decision = analysis.get('decision', {})
        if not decision.get('can_proceed'):
            return {
                "status": "ABORTED",
                "reason": decision.get('blocking_factors') or decision.get('reason') or "Analysis denied execution"
            }
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        data_bundle = {
            "first_name": fn,
            "last_name": ln,
            "username": _gen_username(fn, ln),
            "password": _gen_password(),
            "birthday": _gen_birthday(),
            "phone_number": None,
            "recovery_email": None
        }
        steps: List[Dict[str, Any]] = [
            {"id": "step_1", "action": "NAVIGATE", "target": "https://accounts.google.com/signup"},
            {"id": "step_2", "action": "TYPE", "field": "first_name", "value": data_bundle['first_name'], "description": "input field labeled first name or firstName or given name"},
            {"id": "step_3", "action": "TYPE", "field": "last_name",  "value": data_bundle['last_name'], "description": "input field labeled last name or lastName or surname or family name"},
            {"id": "step_4", "action": "TYPE", "field": "username",   "value": data_bundle['username'], "description": "input field for username or email address"},
            {"id": "step_5", "action": "TYPE", "field": "password",   "value": data_bundle['password'], "description": "input field for password"},
            {"id": "step_6", "action": "TYPE", "field": "birthday",   "value": data_bundle['birthday'], "description": "input field for date of birth or birthday or birth date"},
            {
                "id": "step_7",
                "action": "VERIFY_PAGE_STATE",
                "expected": ["captcha","phone_request","success"],
                "on_result": {
                    "captcha": "step_solve_captcha",
                    "phone_request": {
                        "action": "CHECK_PHONE_AVAILABILITY",
                        "if_available": "step_enter_phone",
                        "if_not_available": "WAITING_USER"
                    },
                    "success": "step_final_verify"
                }
            },
            {"id": "step_solve_captcha", "action": "SOLVE_CAPTCHA", "on_error": {"retry": 3, "else": "WAITING_USER"}, "next": "step_7"},
            {"id": "step_enter_phone", "action": "TYPE", "field": "phone_number", "value": "[WAITING_USER_INPUT]"},
            {"id": "step_final_verify", "action": "VERIFY_SUCCESS"}
        ]
        plan_id = str(uuid.uuid4())
        return {
            "plan_id": plan_id,
            "task_id": req.task_id,
            "strategy": decision.get('strategy', 'attempt_without_phone_fallback_to_user'),
            "steps": steps,
            "data_bundle": data_bundle,
            "expected_outcome": {
                "best_case": "account_created_no_phone_needed",
                "likely_case": "WAITING_USER_for_phone",
                "worst_case": "captcha_unsolvable_after_3_attempts"
            }
        }
    except Exception as e:
        logger.error(f"Generate plan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
