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
# Import automation endpoints for execution
from routes.automation_routes import SmartTypeRequest, SmartClickRequest, smart_type_text, smart_click, FindElementsRequest

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

class AdjustRequest(BaseModel):
    message: str

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
                "steps": current_plan.get('steps') if current_plan else [],
                "hints": current_plan.get('hints') if current_plan else []
            }
        }
        return last_observation
    except Exception as e:
        logger.error(f"[HOOK] observe error: {e}")
        last_observation = {"screenshot_base64": None, "vision": [], "grid": {"rows": 12, "cols": 8}, "status": "error"}
        return last_observation

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
    """Start automation job with planning (analyze → generate) THEN execute."""
    global agent_status, current_session_id, last_observation
    
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
        
        # Step 2: Generate plan
        current_plan = (await planner_generate(GenerateRequest(task_id=current_analysis['task_id'], analysis=current_analysis['analysis'])))
        current_plan.setdefault('hints', [])
        log_step("Plan generated")
        
        # Step 3: Check if we have warm profile
        is_warm = current_analysis.get('analysis', {}).get('availability', {}).get('profile', {}).get('is_warm', False)
        if not is_warm:
            log_step("⚠️ No warm profile, execution paused")
            agent_status = "IDLE"
            return {"status": "PLANNED", "job_id": job_id, "analysis": current_analysis, "plan": current_plan}
        
        # Step 4: Start execution loop
        agent_status = "ACTIVE"
        log_step("🚀 Starting execution loop")
        
        # Get profile and create session
        profile_id = current_analysis.get('analysis', {}).get('availability', {}).get('profile', {}).get('profile_id')
        if not profile_id:
            # Create new profile if needed
            from routes.profile_routes import create_profile
            prof_resp = await create_profile(CreateProfileRequest(warmup=False))
            profile_id = prof_resp.get('profile_id')
        
        # Create browser session
        from services.browser_automation_service import create_session_from_profile
        session_id = await create_session_from_profile(profile_id)
        current_session_id = session_id
        log_step(f"✅ Session created: {session_id}")
        
        # Execute plan steps
        steps = current_plan.get('steps', [])
        data_bundle = current_plan.get('data_bundle', {})
        
        for idx, step in enumerate(steps):
            if agent_status != "ACTIVE":
                log_step(f"⏸️ Execution paused at step {idx+1}")
                break
                
            step_id = step.get('id')
            action = step.get('action')
            log_step(f"Step {idx+1}/{len(steps)}: {action} - {step_id}")
            
            # Execute step based on action type
            try:
                if action == "NAVIGATE":
                    target_url = step.get('target')
                    from services.browser_automation_service import navigate
                    await navigate(session_id, target_url)
                    log_step(f"✅ Navigated to {target_url}", status="ok")
                    
                elif action == "TYPE":
                    field = step.get('field')
                    value = step.get('value') or data_bundle.get(field, '')
                    target_desc = f"field for {field}"
                    # Use smart-type (which uses vision + human typing)
                    from routes.automation_routes import smart_type_endpoint
                    await smart_type_endpoint(SmartTypeRequest(
                        session_id=session_id,
                        description=target_desc,
                        text=value
                    ))
                    log_step(f"✅ Typed '{value}' into {field}", status="ok")
                    
                elif action == "CLICK":
                    target_desc = step.get('target', 'next button')
                    # Use smart-click (which uses vision + human clicking)
                    from routes.automation_routes import smart_click_endpoint
                    await smart_click_endpoint(SmartClickRequest(
                        session_id=session_id,
                        description=target_desc
                    ))
                    log_step(f"✅ Clicked {target_desc}", status="ok")
                    
                elif action == "VERIFY_PAGE_STATE":
                    # Check current page state
                    from services.page_state_service import detect_page_state
                    page_state = await detect_page_state(session_id)
                    log_step(f"📊 Page state: {page_state}", status="ok")
                    
                    # Handle conditional branching
                    on_result = step.get('on_result', {})
                    if page_state in on_result:
                        next_action = on_result[page_state]
                        if next_action == "WAITING_USER":
                            agent_status = "WAITING_USER"
                            log_step(f"⏸️ Waiting for user input: {page_state}")
                            break
                        # TODO: Handle conditional jumps to other steps
                    
                elif action == "USER_HINT":
                    # Just a marker, skip
                    log_step(f"💡 User hint: {step.get('note', '')}", status="ok")
                    continue
                    
                else:
                    log_step(f"⚠️ Unknown action: {action}", status="warning")
                
                # Take screenshot after each step
                from services.browser_automation_service import capture_screenshot
                screenshot_b64 = await capture_screenshot(session_id)
                
                # Store observation
                last_observation = {
                    "screenshot_base64": screenshot_b64,
                    "step_id": step_id,
                    "action": action
                }
                
                # Small delay between steps
                await asyncio.sleep(1.5)
                
            except Exception as step_error:
                log_step(f"❌ Step failed: {str(step_error)}", status="fail")
                agent_status = "ERROR"
                break
        
        # Execution complete
        if agent_status == "ACTIVE":
            agent_status = "IDLE"
            log_step("✅ Execution completed")
        
        return {
            "status": agent_status,
            "job_id": job_id,
            "session_id": current_session_id,
            "analysis": current_analysis,
            "plan": current_plan
        }
        
    except Exception as e:
        logger.error(f"exec error: {e}")
        agent_status = "ERROR"
        log_step(f"❌ Error: {str(e)}", status="fail")
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/adjust')
async def adjust(req: AdjustRequest):
    """User adjustments to current plan during automation run."""
    try:
        global current_plan
        if current_plan is None:
            raise HTTPException(status_code=400, detail="No plan to adjust")
        hint = {"ts": datetime.now().isoformat(), "message": req.message}
        current_plan.setdefault('hints', []).append(hint)
        # Insert a USER_HINT step as a no-op marker the executor can read
        current_plan.setdefault('steps', []).insert(0, {"id": f"hint_{len(current_plan['hints'])}", "action": "USER_HINT", "note": req.message})
        log_step(f"Plan adjusted: {req.message}")
        return {"ok": True, "plan": current_plan}
    except Exception as e:
        logger.error(f"adjust error: {e}")
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
