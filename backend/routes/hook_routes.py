"""
Hook Routes - AI Entry Point API
Universal gateway between user/external AI and internal execution agent
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import logging
import asyncio
import random
import os

from services.browser_automation_service import browser_service
from services.supervisor_service import supervisor_service
from services.anti_detect import HumanBehaviorSimulator
from services.page_state_service import page_state_service
# Import planner endpoints to reuse logic internally
from routes.automation_planner_routes import analyze as planner_analyze, generate as planner_generate, AnalyzeRequest, GenerateRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/hook", tags=["agent-hook"])

# In-memory state (single-runner MVP)
current_profile_id: Optional[str] = None

current_task: Dict[str, Any] = {"text": "", "job_id": None, "timestamp": None}
execution_logs: List[Dict[str, Any]] = []
agent_status: str = "IDLE"  # ACTIVE, PAUSED, WAITING_USER, DONE, ERROR
control_state: Dict[str, Any] = {"run_mode": "PAUSED"}  # ACTIVE, PAUSED, STOP
last_result: Dict[str, Any] = {"screenshot": None, "credentials": None, "completed": False}
last_observation: Dict[str, Any] = {"screenshot_base64": None, "vision": [], "grid": {"rows": 12, "cols": 8}, "status": "idle"}
current_session_id: Optional[str] = None
history_steps: List[Dict[str, Any]] = []
# Pending user input (phone/2FA only)
pending_user_prompt: Optional[str] = None
pending_user_field: Optional[str] = None
pending_user_value: Optional[str] = None
# Planner state
current_analysis: Optional[Dict[str, Any]] = None
current_plan: Optional[Dict[str, Any]] = None

class TaskRequest(BaseModel):
    text: str
    timestamp: int
    nocache: bool = True

class ControlRequest(BaseModel):
    mode: str  # ACTIVE, PAUSED, STOP

class UserInputRequest(BaseModel):
    job_id: str
    field: str
    value: str

# -------- Utilities --------

def log_step(action: str, status: str = "ok", error: Optional[str] = None):
    entry = {
        "ts": datetime.now().isoformat(),
        "step": len(execution_logs) + 1,
        "action": action,
        "status": status,
        "error": error
    }
    execution_logs.append(entry)
    logger.info(f"[HOOK] {action} => {status}")

async def observe(session_id: str):
    global last_observation
    try:
        # Inject and collect DOM + screenshot + vision
        page = browser_service.sessions[session_id]['page']
        await browser_service._inject_grid_overlay(page)
        dom_data = await browser_service._collect_dom_clickables(page)
        screenshot_b64 = await browser_service.capture_screenshot(session_id)
        vision = await browser_service._augment_with_vision(screenshot_b64, dom_data)
        # Detect page state (lightweight)
        try:
            state_info = await page_state_service.detect(page)
            page_state = state_info.get('state', 'unknown')
        except Exception:
            page_state = 'unknown'
        last_observation = {
            "screenshot_base64": screenshot_b64,
            "vision": vision,
            "grid": {"rows": browser_service.grid_rows, "cols": browser_service.grid_cols},
            "viewport": {"width": dom_data.get('vw', 1280), "height": dom_data.get('vh', 800)},
            "status": "idle",
            "url": page.url,
            "page_state": page_state,
            "analysis": current_analysis,
            "plan": {
                "strategy": current_plan.get('strategy') if current_plan else None,
                "steps": current_plan.get('steps') if current_plan else []
            }
        }
        return last_observation
    except Exception as e:
        logger.error(f"[HOOK] observe error: {e}")
        last_observation = {"screenshot_base64": None, "vision": [], "grid": {"rows": 12, "cols": 8}, "status": "error"}
        return last_observation

async def auto_solve_captcha(session_id: str) -> bool:
    """Attempt automatic CAPTCHA solving without user involvement.
       Heuristics: try checkbox/slider/puzzle via grid moves; fallback to VLM solver.
    """
    try:
        obs = await observe(session_id)
        vision = obs.get('vision', [])
        # Simple heuristic: look for captcha keywords
        keywords = ['captcha', "i'm not a robot", 'robot', 'verify', 'challenge']
        slider_types = ['slider']
        checkbox_types = ['checkbox']
        found_keyword = any(any(k in (v.get('label','').lower()) for k in keywords) for v in vision)
        found_slider = any(v.get('type') in slider_types for v in vision)
        found_checkbox = any(v.get('type') in checkbox_types for v in vision)

        # Try checkbox click
        if found_checkbox:
            target = next(v for v in vision if v.get('type') in checkbox_types)
            from services.grid_service import GridConfig
            grid = GridConfig(rows=browser_service.grid_rows, cols=browser_service.grid_cols)
            await browser_service.wait(300)
            page = browser_service.sessions[session_id]['page']
            dom_data = await browser_service._collect_dom_clickables(page)
            vw, vh = dom_data.get('vw', 1280), dom_data.get('vh', 800)
            x, y = grid.cell_to_xy(target['cell'], vw, vh)
            await HumanBehaviorSimulator.human_click(page, x, y)
            await browser_service.wait(600)
            await observe(session_id)
            log_step(f"CAPTCHA checkbox clicked at {target['cell']}")

            return True

        # Try slider drag (drag right within same row by 2 columns)
        if found_slider:
            target = next(v for v in vision if v.get('type') in slider_types)
            from services.grid_service import GridConfig
            grid = GridConfig(rows=browser_service.grid_rows, cols=browser_service.grid_cols)
            cell = target['cell']
            col_letter = cell[0]
            row_num = int(cell[1:])
            to_col_index = min(ord(col_letter) - ord('A') + 2, browser_service.grid_cols - 1)
            to_cell = f"{chr(ord('A') + to_col_index)}{row_num}"
            page = browser_service.sessions[session_id]['page']
            dom_data = await browser_service._collect_dom_clickables(page)
            vw, vh = dom_data.get('vw', 1280), dom_data.get('vh', 800)
            sx, sy = grid.cell_to_xy(cell, vw, vh)
            ex, ey = grid.cell_to_xy(to_cell, vw, vh)
            await HumanBehaviorSimulator.human_drag(page, sx, sy, ex, ey)
            await browser_service.wait(800)
            await observe(session_id)
            log_step(f"CAPTCHA slider drag {cell} → {to_cell}")
            return True

        # Fallback to solver (vision VLM)
        try:
            solved = await browser_service.detect_and_solve_captcha(session_id)
            if solved.get('success'):
                log_step("CAPTCHA solved via VLM solver")
                await observe(session_id)
                return True
        except Exception as e:
            logger.warning(f"[HOOK] captcha solver fallback error: {e}")

    except Exception as e:
        logger.warning(f"[HOOK] auto_solve_captcha error: {e}")
    return False

@router.post('/control')
async def control(req: ControlRequest):
    global agent_status
    try:
        mode = req.mode.upper()
        if mode not in ("ACTIVE","PAUSED","STOP"):
            raise HTTPException(status_code=400, detail="Invalid mode")
        control_state["run_mode"] = mode
        if mode == "PAUSED":
            agent_status = "PAUSED"
        if mode == "STOP":
            agent_status = "IDLE"
        return {"ok": True, "run_mode": control_state["run_mode"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/exec')
async def exec_task(req: TaskRequest):
    """Start automation job with planning (analyze → generate) before execution."""
    try:
        job_id = str(uuid.uuid4())
        current_task["text"] = req.text
        current_task["job_id"] = job_id
        current_task["timestamp"] = req.timestamp
        execution_logs.clear()
        log_step(f"Job started: {job_id}")

        # Step 1: Analyze goal
        global current_analysis, current_plan
        current_analysis = (await planner_analyze(AnalyzeRequest(goal=req.text)))
        log_step("Goal analyzed")
        if not current_analysis.get('analysis', {}).get('decision', {}).get('can_proceed'):
            reason = current_analysis.get('analysis', {}).get('decision', {}).get('reason') or 'cannot proceed'
            log_step(f"Analysis denied: {reason}", status="error")
            return {"status": "ABORTED", "reason": reason, "analysis": current_analysis}

        # Step 2: Generate plan
        current_plan = (await planner_generate(GenerateRequest(task_id=current_analysis['task_id'], analysis=current_analysis['analysis'])))
        log_step("Plan generated")

        # Step 3: Prepare profile/session
        from services.profile_service import profile_service
        warm_meta = current_analysis['analysis']['availability']
        # Use found warm profile if any; else create one
        prof_id = warm_meta.get('profile_id') if warm_meta.get('profile_id') else None
        if not prof_id:
            prof = await profile_service.create_profile(region=None, proxy_tier=None)
            prof_id = prof['profile_id']
        use = await profile_service.use_profile(prof_id)
        global current_session_id, current_profile_id
        current_profile_id = prof_id
        current_session_id = use['session_id']
        log_step(f"Session from profile {prof_id} created")

        # Navigate initial if plan says so
        first_step = current_plan.get('steps', [{}])[0]
        if first_step and first_step.get('action') == 'NAVIGATE' and first_step.get('target'):
            await browser_service.navigate(current_session_id, first_step['target'])
            await observe(current_session_id)
            log_step(f"Navigated to {first_step['target']}")

        return {"status": "PLANNED", "job_id": job_id, "analysis": current_analysis, "plan": current_plan}
    except Exception as e:
        logger.error(f"exec error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/log')
async def get_log():
    return {
        "task": current_task,
        "status": agent_status,
        "logs": execution_logs,
        "observation": last_observation,
        "session_id": current_session_id,
        "plan": current_plan
    }
