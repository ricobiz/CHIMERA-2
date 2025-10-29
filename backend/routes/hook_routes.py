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
from services.head_brain_service import head_brain_service
# Import automation endpoints for execution
from routes.automation_routes import SmartTypeRequest, SmartClickRequest, smart_type_text, smart_click, FindElementsRequest
from routes.profile_routes import CreateProfileRequest

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
    """Start automation with HEAD BRAIN → Spinal Cord (Brain) loop → Executor."""
    global agent_status, current_session_id, last_observation, current_analysis, current_plan
    
    try:
        job_id = str(uuid.uuid4())
        current_task["text"] = req.text
        current_task["job_id"] = job_id
        current_task["timestamp"] = req.timestamp
        execution_logs.clear()
        log_step(f"Job started: {job_id}")
        
        goal = req.text
        
        # ============================================================
        # PHASE 1: ГОЛОВНОЙ МОЗГ (Head Brain) - ОДИН РАЗ В НАЧАЛЕ
        # ============================================================
        log_step("🧠 [HEAD BRAIN] Analyzing task and creating strategy...")
        
        # Получаем информацию о доступном профиле
        from routes.automation_planner_routes import _find_warm_profile
        warm_meta = _find_warm_profile()
        profile_info = None
        if warm_meta:
            profile_info = {
                "profile_id": warm_meta.get('profile_id'),
                "is_warm": warm_meta.get('warmup', {}).get('is_warm') or warm_meta.get('status') in ('warm', 'active'),
                "proxy_type": (warm_meta.get('proxy', {}) or {}).get('proxy_type')
            }
        
        # Вызываем головной мозг для анализа и планирования
        head_analysis = await head_brain_service.analyze_and_plan(goal, profile_info)
        
        # Сохраняем результаты анализа
        current_analysis = {
            "task_id": head_analysis['task_id'],
            "analysis": {
                "understood_task": head_analysis['understood_task'],
                "requirements": head_analysis['requirements'],
                "availability": {
                    "profile": head_analysis.get('profile_status', {}),
                    "can_proceed_without_warm": not head_analysis['requirements'].get('needs_phone', False)
                },
                "decision": {
                    "can_proceed": head_analysis['can_proceed'],
                    "strategy": head_analysis['strategy'],
                    "success_probability": head_analysis['success_probability'],
                    "reason": head_analysis['reason']
                }
            }
        }
        
        # План для спинного мозга
        current_plan = {
            "strategy": head_analysis['strategy'],
            "plan_outline": head_analysis.get('plan_outline', ''),
            "data_bundle": head_analysis['data_bundle']
        }
        
        # Get generated data (name, username, password, etc)
        data_bundle = head_analysis['data_bundle']
        log_step(f"✅ [HEAD BRAIN] Strategy: {head_analysis['strategy']}")
        log_step(f"✅ [HEAD BRAIN] Data generated: {list(data_bundle.keys())}")
        
        # Проверяем можем ли продолжить
        if not head_analysis['can_proceed']:
            log_step(f"⚠️ [HEAD BRAIN] Cannot proceed: {head_analysis['reason']}")
            agent_status = "IDLE"
            return {
                "status": "NEEDS_REQUIREMENTS",
                "job_id": job_id,
                "analysis": current_analysis,
                "message": head_analysis['reason']
            }
        
        agent_status = "ACTIVE"
        
        # Phase 3: Create session
        profile_id = profile_info.get('profile_id')
        if not profile_id:
            from routes.profile_routes import create_profile, CreateProfileRequest
            prof_resp = await create_profile(CreateProfileRequest(warmup=False))
            profile_id = prof_resp.get('profile_id')
        
        session_id = str(uuid.uuid4())
        await browser_service.create_session_from_profile(
            profile_id=profile_id,
            session_id=session_id
        )
        current_session_id = session_id
        log_step(f"✅ Session created: {session_id}")
        
        # Phase 4: Brain-driven loop
        history = []
        max_steps = 50
        step_count = 0
        
        while agent_status == "ACTIVE" and step_count < max_steps:
            step_count += 1
            log_step(f"🧠 Brain cycle {step_count}/{max_steps}")
            
            # 1. Screenshot + Vision
            screenshot_b64 = await browser_service.capture_screenshot(session_id)
            vision_elements = await browser_service.find_elements_with_vision(session_id, "all interactive elements")
            
            # 2. Ask Brain with CONTEXT (goal + data_bundle)
            brain_context = {
                "goal": goal,
                "data_available": data_bundle,  # Brain знает что у нас есть имя/пароль/etc
                "history": history
            }
            
            brain_result = await supervisor_service.next_step(
                goal=f"{goal} | Available data: {list(data_bundle.keys())}",
                history=history,
                screenshot_base64=screenshot_b64,
                vision=vision_elements or [],
                model='qwen/qwen2.5-vl'
            )
            
            action = brain_result.get('action')
            log_step(f"🧠 Brain says: {action}")
            
            # 3. Execute
            if action == 'CLICK':
                target = brain_result.get('target')
                log_step(f"👆 Clicking {target}")
                await browser_service.click_cell(session_id, target)
                
            elif action == 'TYPE':
                target = brain_result.get('target')
                value = brain_result.get('value')
                log_step(f"⌨️  Typing '{value}' at {target}")
                await browser_service.type_at_cell(session_id, target, value)
                
            elif action == 'NAVIGATE':
                url = brain_result.get('url')
                log_step(f"🌐 Navigating to {url}")
                await browser_service.navigate(session_id, url)
                
            elif action == 'WAIT':
                log_step(f"⏳ Waiting...")
                await asyncio.sleep(2)
                
            elif action == 'DONE':
                log_step(f"✅ Brain says DONE")
                agent_status = "IDLE"
                break
                
            elif action == 'WAITING_USER':
                log_step(f"⏸️  Waiting for user input")
                agent_status = "WAITING_USER"
                break
            
            # 4. History
            history.append({
                "step": step_count,
                "action": action,
                "target": brain_result.get('target'),
                "result": "executed"
            })
            
            last_observation = {
                "screenshot_base64": screenshot_b64,
                "step": step_count,
                "action": action
            }
            
            await asyncio.sleep(1.5)
        
        if step_count >= max_steps:
            log_step(f"⚠️  Max steps reached")
            agent_status = "ERROR"
        
        log_step(f"🏁 Execution finished")
        
        return {
            "status": agent_status,
            "job_id": job_id,
            "session_id": current_session_id,
            "steps_executed": step_count
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
