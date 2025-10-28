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
        last_observation = {
            "screenshot_base64": screenshot_b64,
            "vision": vision,
            "grid": {"rows": browser_service.grid_rows, "cols": browser_service.grid_cols},
            "status": "idle",
            "url": page.url
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

async def run_task_loop(job_id: str, goal_text: str):
    global agent_status, last_result, current_session_id, history_steps, pending_user_prompt, pending_user_field, pending_user_value
    try:
        agent_status = "ACTIVE"
        control_state["run_mode"] = "ACTIVE"
        # Prepare creds for Gmail
        base_user = f"{uuid.uuid4().hex[:8]}{random.randint(10,99)}"
        password = f"{uuid.uuid4().hex[:6]}A!{random.randint(1000,9999)}"
        credentials = {"login": f"{base_user}", "password": password}

        # Ensure we have a clean profile
        from services.profile_service import profile_service
        # For MVP: always create a new profile; later we can reuse existing good ones
        prof = await profile_service.create_profile(region=None, proxy_tier=None)
        if not prof.get('is_clean', False):
            # Do NOT abort; warn and continue to allow testing/runs even if checker is pessimistic
            log_step("Profile flagged by checker; proceeding with caution.", status="warning")
        # Use profile for this run
        global current_profile_id
        current_profile_id = prof['profile_id']
        # Spin session from the profile
        use = await profile_service.use_profile(prof['profile_id'])
        session_id = use['session_id']
        current_session_id = session_id
        log_step(f"Session from profile {prof['profile_id']} created")

        # Navigate to Gmail signup
        await browser_service.navigate(session_id, "https://accounts.google.com/signup")
        log_step("Navigated to Gmail signup")
        await observe(session_id)

        history_steps = []
        pending_user_prompt = None
        pending_user_field = None
        pending_user_value = None

        # Main loop
        while True:
            # Respect control state
            if control_state.get("run_mode") == "PAUSED":
                await asyncio.sleep(0.5)
                continue
            if control_state.get("run_mode") == "STOP":
                agent_status = "IDLE"
                log_step("Stopped by user", status="info")
                return

            # Handle WAITING_USER resume
            if agent_status == "WAITING_USER":
                if pending_user_value:
                    agent_status = "ACTIVE"
                    # Include user input into next brain prompt
                    history_steps.append({"action": "USER_INPUT", "field": pending_user_field, "value": pending_user_value})
                    log_step(f"User provided {pending_user_field}: ******", status="ok")
                else:
                    await asyncio.sleep(0.5)
                    continue

            # Try solve CAPTCHA opportunistically
            await auto_solve_captcha(session_id)

            obs = await observe(session_id)
            screenshot_b64 = obs.get('screenshot_base64')
            vision = obs.get('vision', [])

            # Build goal with any known creds + user input (masked)
            extra = ""
            if pending_user_value:
                extra += f"\nUser provided {pending_user_field}: AVAILABLE."
                # clear after injecting once
                pending_user_prompt = None
                pending_user_field = None
                pending_user_value = None

            decision = await supervisor_service.next_step(
                goal=goal_text + f"\nUse prepared credentials: username={credentials['login']}, password={credentials['password']}." + extra,
                history=history_steps,
                screenshot_base64=screenshot_b64,
                vision=vision,
                model=os.environ.get('AUTOMATION_VLM_MODEL', 'qwen/qwen2.5-vl')
            )

            if decision.get('error'):
                log_step(f"Brain error: {decision.get('error')}", status="error")
                agent_status = "ERROR"
                break

            # Handle needs_user_input only for phone/2FA
            if decision.get('needs_user_input'):
                ask = (decision.get('ask_user') or '').lower()

                if any(k in ask for k in ['phone', 'sms', '2fa', 'code', 'номер', 'смс']):
                    agent_status = "WAITING_USER"
                    pending_user_prompt = decision.get('ask_user') or 'Provide required input'
                    # Try infer field type
                    pending_user_field = 'phone' if 'phone' in ask or 'номер' in ask else 'code'
                    log_step(f"WAITING_USER: {pending_user_prompt}", status="info")
                    await asyncio.sleep(0.5)
                    continue
                else:
                    # Do not block on captchas — continue
                    log_step("Brain requested user input, ignored (non-2FA)", status="warning")

            action = (decision.get('next_action') or '').upper()
            target_cell = decision.get('target_cell')
            text = decision.get('text', '')
            direction = decision.get('direction', 'down')
            amount = int(decision.get('amount', 400) or 400)

            try:
                if action == 'CLICK_CELL' and target_cell:
                    # use anti-detect human click
                    from services.grid_service import GridConfig
                    page = browser_service.sessions[session_id]['page']
                    dom_data = await browser_service._collect_dom_clickables(page)
                    vw, vh = dom_data.get('vw', 1280), dom_data.get('vh', 800)
                    grid = GridConfig(rows=browser_service.grid_rows, cols=browser_service.grid_cols)
                    x, y = grid.cell_to_xy(target_cell, vw, vh)
                    await HumanBehaviorSimulator.human_click(page, x, y)
                elif action == 'TYPE_AT_CELL' and target_cell:
                    # Fill with prepared creds if text hints empty
                    if not text:
                        label = next((v.get('label','').lower() for v in vision if v.get('cell') == target_cell), '')
                        if any(k in label for k in ['user', 'email', 'gmail', 'логин']):
                            text = credentials['login']
                        elif any(k in label for k in ['pass', 'парол']):
                            text = credentials['password']
                    from services.grid_service import GridConfig
                    page = browser_service.sessions[session_id]['page']
                    dom_data = await browser_service._collect_dom_clickables(page)
                    vw, vh = dom_data.get('vw', 1280), dom_data.get('vh', 800)
                    grid = GridConfig(rows=browser_service.grid_rows, cols=browser_service.grid_cols)
                    x, y = grid.cell_to_xy(target_cell, vw, vh)
                    await HumanBehaviorSimulator.human_move(page, x, y)
                    await page.mouse.click(x, y)
                    await page.keyboard.type(text or "test", delay=50)
                elif action == 'HOLD_DRAG' and target_cell and isinstance(decision.get('to_cell', None), str):
                    from_cell = target_cell
                    to_cell = decision['to_cell']
                    from services.grid_service import GridConfig
                    page = browser_service.sessions[session_id]['page']
                    dom_data = await browser_service._collect_dom_clickables(page)
                    vw, vh = dom_data.get('vw', 1280), dom_data.get('vh', 800)
                    grid = GridConfig(rows=browser_service.grid_rows, cols=browser_service.grid_cols)
                    sx, sy = grid.cell_to_xy(from_cell, vw, vh)
                    ex, ey = grid.cell_to_xy(to_cell, vw, vh)
                    await HumanBehaviorSimulator.human_drag(page, sx, sy, ex, ey)
                elif action == 'SCROLL':
                    dy = amount if direction == 'down' else -abs(amount)
                    await browser_service.scroll(session_id, 0, dy)
                elif action == 'WAIT':
                    await browser_service.wait(amount)
                elif action == 'DONE':
                    agent_status = "DONE"
                    log_step("Task finished (brain signaled DONE)", status="ok")
                    break
                else:
                    log_step(f"Unknown action: {action}", status="warning")

                # After action, observe again and record
                await observe(session_id)
                history_steps.append({"action": action, "cell": target_cell, "text": (text[:20] if text else '')})
                qt = (f'"{text}"') if text else ''
                log_step(f"Step {len(execution_logs)+1}: {action} {target_cell or ''} {qt} → ok")
            except Exception as e:
                log_step(f"Step error: {action} {target_cell or ''}", status="error", error=str(e))
                await asyncio.sleep(0.5)

        # Finalize result
        last_result["completed"] = (agent_status == "DONE")
        last_result["credentials"] = {"login": f"{credentials['login']}@gmail.com", "password": credentials['password']}
        last_result["screenshot"] = last_observation.get('screenshot_base64')
        if agent_status == "DONE":
            agent_status = "IDLE"

    except Exception as e:
        agent_status = "ERROR"
        log_step(f"Fatal error: {str(e)}", status="error")

# --------- Endpoints ---------

@router.post("/exec")
async def execute_task(request: TaskRequest):
    """Kick off real automation loop in background."""
    global current_task, agent_status, execution_logs, history_steps
    try:
        job_id = str(uuid.uuid4())
        current_task = {"text": request.text, "job_id": job_id, "timestamp": request.timestamp}
        execution_logs = []
        history_steps = []
        agent_status = "ACTIVE"
        asyncio.create_task(run_task_loop(job_id, request.text))
        log_step(f"Task accepted: {request.text[:80]}...")
        return {"status": "accepted", "job_id": job_id, "message": "Task accepted for execution"}
    except Exception as e:
        agent_status = "ERROR"
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/log")
async def get_logs(nocache: int = 1, ts: Optional[int] = None, read: bool = False):
    try:
        return {
            "logs": execution_logs,
            "status": agent_status,
            "job_id": current_task.get('job_id'),
            "result_ready": last_result.get('completed', False),
            "total_steps": len(execution_logs),
            "timestamp": datetime.now().isoformat(),
            "observation": last_observation,
            "session_id": current_session_id,
            "ask_user": pending_user_prompt if agent_status == "WAITING_USER" else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/refresh")
async def refresh_agent(target: str = "main", nocache: int = 1, timestamp: Optional[int] = None):
    try:
        return {"status": "refresh_ok", "target": target}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/text")
async def get_current_text():
    try:
        return {"text": current_task.get("text", ""), "job_id": current_task.get("job_id"), "timestamp": current_task.get("timestamp")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/result")
async def get_result(nocache: int = 1, timestamp: Optional[int] = None):
    try:
        return {"success": True, "result": last_result, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/result_bundle")
async def get_result_bundle(job_id: Optional[str] = None):
    try:
        if not last_result.get('completed'):
            return {"success": False, "message": "Result bundle not ready yet"}
        bundle = {
            "credentials": last_result.get('credentials'),
            "screenshot": last_result.get('screenshot'),
            "status": "success" if last_result.get('completed') else "failed",
            "job_id": current_task.get('job_id')
        }
        return {"success": True, "result_bundle": bundle}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/control")
async def control_agent(request: ControlRequest):
    global control_state, agent_status
    try:
        if request.mode not in ["ACTIVE", "PAUSED", "STOP"]:
            raise HTTPException(status_code=400, detail="Invalid mode. Must be ACTIVE, PAUSED, or STOP")
        control_state["run_mode"] = request.mode
        if request.mode == "ACTIVE" and agent_status in ["IDLE", "WAITING_USER"]:
            agent_status = "ACTIVE"
        elif request.mode == "PAUSED":
            agent_status = "IDLE"
        elif request.mode == "STOP":
            agent_status = "IDLE"
        return {"success": True, "run_mode": control_state["run_mode"], "agent_status": agent_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/user_input")
async def provide_user_input(req: UserInputRequest):
    """Provide user input (phone/2FA) when agent is WAITING_USER"""
    global pending_user_prompt, pending_user_field, pending_user_value, agent_status
    try:
        if current_task.get('job_id') != req.job_id:
            raise HTTPException(status_code=400, detail="Job mismatch")
        pending_user_field = req.field
        pending_user_value = req.value
        # Do not flip status here; loop will resume and switch to ACTIVE
        log_step(f"User input received for {req.field}", status="ok")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_agent_status():
    return {
        "status": agent_status,
        "current_task": current_task.get("text", ""),
        "job_id": current_task.get("job_id"),
        "active": agent_status == "ACTIVE",
        "run_mode": control_state["run_mode"],
        "completed": last_result["completed"],
        "session_id": current_session_id
    }
