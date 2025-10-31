"""
Hook Routes - AI Entry Point API
Universal gateway between user/external AI and internal execution agent
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
import time
from datetime import datetime
import logging
import asyncio
import random
import os
from faker import Faker

from services.browser_automation_service import browser_service
from services.supervisor_service import supervisor_service
from services.anti_detect import HumanBehaviorSimulator
from services.page_state_service import page_state_service
from services.head_brain_service import head_brain_service
from services.form_filler_service import form_filler_service
from services.planner_service import planner_service
from services.scene_builder_service import SceneBuilderService
# Import automation endpoints for execution
from routes.automation_routes import SmartTypeRequest, SmartClickRequest, smart_type_text, smart_click, FindElementsRequest
from routes.profile_routes import CreateProfileRequest

# NEW: Import autonomous agent
from automation import autonomous_agent

logger = logging.getLogger(__name__)

# Initialize Faker for data generation
fake = Faker(['en_US'])

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
# Planner state (NEW STRUCTURE - plan-based execution)
current_analysis: Optional[Dict[str, Any]] = None
current_plan: Optional[Dict[str, Any]] = None  # {strategy, steps: [{id, action, target, field, on_error, next}], hints}
current_step_id: Optional[str] = None  # ID текущего шага из плана
data_bundle: Dict[str, Any] = {}  # Сгенерированные данные (first_name, password и т.д.)
policy: Dict[str, Any] = {}  # Политики и ограничения (name_generation_hint, stop_before_phone и т.д.)
override_buffer: List[str] = []  # Очередь операторских указаний для применения
# Automation chat history (отдельно от main chat)
automation_chat_history: List[Dict[str, Any]] = []

class TaskRequest(BaseModel):
    text: str
    timestamp: int
    nocache: bool = True
    user_data: Optional[Dict[str, Any]] = None  # Данные пользователя (опционально)

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

@router.post('/exec-autonomous')
async def exec_autonomous_task(req: TaskRequest):
    """Start autonomous automation with bulletproof reliability"""
    global agent_status
    try:
        # Setup WebSocket callback for real-time updates
        async def websocket_callback(event: Dict[str, Any]):
            nonlocal agent_status
            # In a real implementation, this would send to actual WebSocket clients
            # For now, we'll log events and update internal state
            logger.info(f"🔄 [AUTONOMOUS] Event: {event['type']}")
            
            # Update internal state for /log endpoint compatibility
            if event['type'] == 'task_started':
                current_task["text"] = req.text
                current_task["job_id"] = event.get('task_id')
                current_task["timestamp"] = req.timestamp
            
            elif event['type'] == 'step_completed':
                log_step(f"Step {event['data']['step_index']}: {event['data']['step']['action']}")
            
            elif event['type'] == 'tool_executed':
                log_step(f"Tool executed: {event['data']['tool']}")
            
            elif event['type'] == 'task_completed':
                agent_status = "DONE"
                log_step("🎉 Autonomous task completed successfully!")
            
            elif event['type'] == 'task_failed':
                agent_status = "ERROR"
                log_step(f"❌ Autonomous task failed: {event['data'].get('error', 'Unknown error')}")
        
        # Set up agent with callback
        autonomous_agent.ws_callback = websocket_callback
        
        # Create context from request
        context = {
            "timeout": 900,  # 15 minutes
            "max_retries": 3,
            "use_proxy": True
        }
        
        # Execute autonomous task
        result = await autonomous_agent.run(
            goal=req.text,
            context=context,
            user_data=req.user_data
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Autonomous exec error: {e}")
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
        # auto_generate = TRUE если пользователь НЕ предоставил данные (генерируем автоматически)
        auto_generate = req.user_data is None or not req.user_data
        head_analysis = await head_brain_service.analyze_and_plan(goal, profile_info, req.user_data, auto_generate)
        
        # Проверяем статус
        if head_analysis.get('status') == 'NEEDS_USER_DATA':
            log_step("⏸️ [HEAD BRAIN] Waiting for user data")
            log_step(f"📋 Required fields: {', '.join(head_analysis['required_fields'])}")
            agent_status = "IDLE"
            return {
                "status": "NEEDS_USER_DATA",
                "job_id": job_id,
                "task_id": head_analysis['task_id'],
                "target_url": head_analysis.get('target_url'),
                "understood_task": head_analysis.get('understood_task'),
                "required_fields": head_analysis['required_fields'],
                "optional_fields": head_analysis.get('optional_fields', []),
                "message": head_analysis['message']
            }
        
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
        
        # План для спинного мозга (НОВЫЙ ФОРМАТ с детальными шагами)
        current_plan = {
            "strategy": head_analysis['strategy'],
            "plan_outline": head_analysis.get('plan_outline', ''),
            "steps": head_analysis.get('steps', []),  # ДЕТАЛЬНЫЙ ПЛАН ШАГОВ
            "data_bundle": head_analysis['data_bundle'],
            "hints": []  # Операторские подсказки
        }
        
        # Инициализация глобальных переменных для plan-based execution
        global data_bundle, current_step_id, policy
        data_bundle = head_analysis['data_bundle']
        
        # Устанавливаем первый шаг из плана
        if current_plan.get('steps'):
            current_step_id = current_plan['steps'][0].get('id')
            log_step(f"📍 [PLAN] Starting from step: {current_step_id}")
        else:
            current_step_id = None
            log_step("⚠️ [PLAN] No detailed steps in plan, using fallback mode")
        
        # Инициализация политики (по умолчанию)
        policy = {
            "name_generation_hint": "real human name without digits",
            "stop_before_phone": False,
            "wait_before_action": False
        }
        
        data_source = head_analysis.get('data_source', 'generated')
        log_step(f"✅ [HEAD BRAIN] Strategy: {head_analysis['strategy']}")
        log_step(f"✅ [HEAD BRAIN] Data source: {data_source}")
        log_step(f"📋 [HEAD BRAIN] Data: {', '.join([f'{k}={v[:20]}...' if isinstance(v, str) and len(v) > 20 else f'{k}={v}' for k, v in data_bundle.items() if v])}")
        
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
        
        # ============================================================
        # PHASE 2: СОЗДАНИЕ/ПРОГРЕВ ПРОФИЛЯ
        # ============================================================
        needs_warm = head_analysis['requirements'].get('needs_warm_profile', False)
        profile_id = profile_info.get('profile_id') if profile_info else None
        
        if not profile_id:
            from routes.profile_routes import create_profile, CreateProfileRequest
            if needs_warm:
                log_step("🔥 Creating and warming up profile (60 seconds)...")
            else:
                log_step("📦 Creating new profile...")
            
            prof_resp = await create_profile(CreateProfileRequest(warmup=needs_warm, region="US"))
            profile_id = prof_resp.get('profile_id')
            
            if needs_warm:
                log_step(f"✅ Profile warmed up: {profile_id}")
        
        session_id = str(uuid.uuid4())
        await browser_service.create_session_from_profile(
            profile_id=profile_id,
            session_id=session_id
        )
        current_session_id = session_id
        log_step(f"✅ Session created: {session_id} with profile: {profile_id}")
        
        # ============================================================
        # PHASE 3: ЦИКЛ "СПИННОЙ МОЗГ + ИСПОЛНИТЕЛЬ"
        # Спинной мозг (Supervisor) принимает решения
        # Исполнитель (Local Vision) видит экран и выполняет
        # ============================================================
        history = []
        max_steps = 150  # Increased for complex registration flows
        step_count = 0
        
        log_step(f"🔄 [SPINAL CORD] Starting execution loop (max {max_steps} steps)")
        
        # ВАЖНО: Используем URL от головного мозга
        start_url = head_analysis.get('target_url', '')
        
        if start_url:
            log_step(f"📍 [HEAD BRAIN] Target URL: {start_url}")
        else:
            # Fallback - извлекаем из задачи пользователя
            import re
            url_match = re.search(r'https?://[^\s]+', goal)
            if url_match:
                start_url = url_match.group(0)
                log_step(f"📍 Extracted URL from goal (fallback): {start_url}")
            elif 'gmail' in goal.lower() or 'google' in goal.lower():
                start_url = "https://accounts.google.com/signup"
                log_step(f"📍 Detected Gmail task, using: {start_url}")
            else:
                start_url = None
                log_step("⚠️ No URL found. Will rely on Brain to navigate.")
        
        # ОБЯЗАТЕЛЬНАЯ начальная навигация
        current_url = "about:blank"
        if start_url:
            try:
                log_step(f"🌐 [INITIAL] Navigating to {start_url}")
                nav_result = await browser_service.navigate(session_id, start_url)
                current_url = nav_result.get('url', start_url)
                log_step(f"✅ [INITIAL] Navigation successful, current URL: {current_url}")
                await asyncio.sleep(2)  # Дать странице загрузиться
            except Exception as e:
                log_step(f"❌ [INITIAL] Navigation failed: {str(e)}")
                current_url = "about:blank"
        
        # ============================================================
        # PHASE 2.5: GENERATE DETAILED PLAN USING PLANNER (NEW!)
        # ============================================================
        log_step("🧩 [PLANNER] Building detailed execution plan from current scene...")
        try:
            # Build Scene JSON from current page
            scene_builder = SceneBuilderService()
            page = browser_service.sessions[session_id]['page']
            dom_data = await browser_service._collect_dom_clickables(page)
            screenshot_b64 = await browser_service.capture_screenshot(session_id)
            vision_elements = await browser_service._augment_with_vision(screenshot_b64, dom_data)
            
            scene = await scene_builder.build_scene(
                page=page,
                dom_data=dom_data,
                vision_elements=vision_elements,
                session_id=session_id
            )
            
            # Call Planner to generate detailed steps
            goal_for_planner = {
                "site": current_url,
                "task": "fill_form" if "register" in goal.lower() or "signup" in goal.lower() else "navigate",
                "description": goal
            }
            
            plan_result = await planner_service.decide_plan(
                goal=goal_for_planner,
                scene=scene,
                context={"data": data_bundle}
            )
            
            if plan_result.get('success') and plan_result.get('plan'):
                detailed_plan = plan_result['plan']
                candidates = detailed_plan.get('candidates', [])
                chosen_id = detailed_plan.get('chosen', 'A')
                
                # Find chosen candidate
                chosen_candidate = next((c for c in candidates if c['id'] == chosen_id), None)
                if chosen_candidate and chosen_candidate.get('steps'):
                    current_plan['steps'] = chosen_candidate['steps']
                    current_plan['plan_outline'] = chosen_candidate.get('why', '')
                    log_step(f"✅ [PLANNER] Generated {len(chosen_candidate['steps'])} steps for candidate {chosen_id}")
                    log_step(f"📋 [PLANNER] Plan: {chosen_candidate.get('why', 'No description')}")
                else:
                    log_step("⚠️ [PLANNER] No steps in chosen candidate, using fallback")
            else:
                log_step(f"⚠️ [PLANNER] Planning failed: {plan_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Planner error: {e}")
            log_step(f"❌ [PLANNER] Error: {str(e)}")
        
        # ============================================================
        # PHASE 3: PLAN-BASED EXECUTION LOOP (NEW ARCHITECTURE)
        # ============================================================
        # Данные для использования в автоматизации
        used_data = data_bundle
        
        # Tracking which textboxes have been filled (to avoid filling same field twice)
        filled_textbox_cells = set()
        
        # Получаем план шагов
        plan_steps = current_plan.get('steps', [])
        if not plan_steps:
            log_step("⚠️ [PLAN] No steps in plan, using fallback mode")
            # Fallback на старую логику если плана нет
            # (оставляем это как safety net, но основной путь - план)
        
        log_step(f"📋 [PLAN] Total steps in plan: {len(plan_steps)}")
        
        # Initialize current_step_id from first step in plan
        if plan_steps and len(plan_steps) > 0:
            # Planner uses different format: steps are objects with "action", "target", etc
            # Need to assign IDs if not present
            for idx, step in enumerate(plan_steps):
                if 'id' not in step:
                    step['id'] = f"step_{idx+1}"
            current_step_id = plan_steps[0].get('id', 'step_1')
            log_step(f"📍 [PLAN] Starting from step: {current_step_id}")
        else:
            current_step_id = None
            log_step("⚠️ [PLAN] No current_step_id set, execution will not start")
        
        # Счётчик попыток retry для текущего шага
        step_retry_count = 0
        max_retries_per_step = 3
        
        while agent_status == "ACTIVE" and current_step_id and step_count < max_steps:
            step_count += 1
            log_step(f"🔄 [CYCLE {step_count}/{max_steps}] Step: {current_step_id}")
            
            # ============================================================
            # STEP 1: APPLY OVERRIDE BUFFER (операторские указания)
            # ============================================================
            if override_buffer:
                log_step(f"📝 [OVERRIDE] Applying {len(override_buffer)} operator instructions")
                for override_msg in override_buffer:
                    log_step(f"  → {override_msg}")
                    # Политики уже обновлены в /adjust endpoint
                override_buffer.clear()
                log_step(f"✅ [OVERRIDE] Applied. Current policy: {policy}")
            
            # ============================================================
            # STEP 2: GET CURRENT STEP FROM PLAN
            # ============================================================
            current_step = None
            for step in plan_steps:
                if step.get('id') == current_step_id:
                    current_step = step
                    break
            
            if not current_step:
                log_step(f"❌ [PLAN] Step {current_step_id} not found in plan!")
                agent_status = "ERROR"
                break
            
            step_action = (current_step.get('action') or '').upper()  # Normalize to uppercase
            step_field = current_step.get('field')
            step_target_raw = current_step.get('target')
            # Handle target: can be string or dict with {by, value}
            if isinstance(step_target_raw, dict):
                step_target = step_target_raw.get('value', '')
                step_target_by = step_target_raw.get('by', 'label')
            else:
                step_target = step_target_raw
                step_target_by = 'label'
            
            step_data_key = current_step.get('data_key')
            step_next = current_step.get('next')
            step_on_error = current_step.get('on_error', 'retry_with_fix')
            
            log_step(f"📋 [PLAN] Executing step: {step_action} (field={step_field}, target={step_target})")
            
            # ============================================================
            # STEP 3: WAIT FOR PAGE READY
            # ============================================================
            try:
                page = browser_service.sessions[session_id]['page']
                loading_status = await browser_service.is_page_loading(page)
                
                if loading_status.get('is_loading'):
                    reason = loading_status.get('reason')
                    log_step(f"⏳ [EXECUTOR] Page still loading: {reason}")
                    await browser_service.wait_for_page_ready(page, timeout_ms=5000)
                    log_step("✅ [EXECUTOR] Page ready")
            except Exception as e:
                log_step(f"⚠️ [EXECUTOR] Loading check failed: {str(e)}")
            
            # ============================================================
            # STEP 4: EXECUTE ACTION THROUGH human_* METHODS
            # ============================================================
            action_executed = False
            action_error = None
            
            try:
                page = browser_service.sessions[session_id]['page']
                current_url = page.url
                
                if step_action == 'NAVIGATE':
                    # Навигация на URL
                    target_url = step_target or start_url
                    log_step(f"🌐 [EXECUTOR] human_navigate to {target_url}")
                    await browser_service.navigate(session_id, target_url)
                    await asyncio.sleep(random.uniform(2.0, 3.5))  # human reaction time
                    action_executed = True
                    
                elif step_action == 'TYPE':
                    # Ввод текста через human_type
                    # Получаем значение из data_bundle
                    if step_data_key and step_data_key in used_data:
                        text_to_type = str(used_data[step_data_key])
                    else:
                        text_to_type = step_target or ""
                    
                    if not text_to_type:
                        log_step(f"⚠️ [EXECUTOR] No text to type for field {step_field}")
                        action_error = f"Missing data for {step_data_key}"
                    else:
                        log_step(f"⌨️  [EXECUTOR] human_type '{text_to_type[:30]}...' for field {step_field}")
                        
                        # Найти элемент по field name или использовать vision
                        await browser_service._inject_grid_overlay(page)
                        dom_data = await browser_service._collect_dom_clickables(page)
                        screenshot_b64 = await browser_service.capture_screenshot(session_id)
                        vision_elements = await browser_service._augment_with_vision(screenshot_b64, dom_data)
                        
                        # Ищем поле в vision по field name с улучшенной логикой
                        target_cell = None
                        textbox_elements = [el for el in vision_elements if el.get('type', '').lower() in ['input', 'textarea', 'textbox']]
                        
                        # First try: exact match by field name in label or aria-label
                        for el in textbox_elements:
                            el_cell = el.get('cell')
                            if el_cell in filled_textbox_cells:
                                continue  # Skip already filled fields
                            
                            el_label = (el.get('label') or '').lower()
                            el_aria = (el.get('aria_label') or '').lower()
                            if step_field and (step_field.lower() in el_label or step_field.lower() in el_aria):
                                target_cell = el_cell
                                log_step(f"📍 [EXECUTOR] Found field {step_field} by label match at {target_cell}")
                                break
                        
                        # Second try: find first EMPTY/unfilled textbox
                        if not target_cell:
                            for el in textbox_elements:
                                el_cell = el.get('cell')
                                if el_cell in filled_textbox_cells:
                                    continue  # Skip already filled
                                
                                el_label = (el.get('label') or '').strip()
                                # Empty if label is generic or very short
                                if el_label in ['INPUT', 'textbox', '1', ''] or len(el_label) <= 3:
                                    target_cell = el_cell
                                    log_step(f"📍 [EXECUTOR] Using first unfilled textbox at {target_cell}")
                                    break
                        
                        # Third try: use any unfilled textbox as fallback
                        if not target_cell:
                            for el in textbox_elements:
                                el_cell = el.get('cell')
                                if el_cell not in filled_textbox_cells:
                                    target_cell = el_cell
                                    log_step(f"⚠️ [EXECUTOR] Using first available unfilled textbox at {target_cell} as fallback")
                                    break
                        
                        if target_cell:
                            result = await browser_service.type_at_cell(session_id, target_cell, text_to_type, human_like=True)
                            if result.get('success'):
                                action_executed = True
                                filled_textbox_cells.add(target_cell)  # Mark as filled
                                log_step(f"✅ [EXECUTOR] Typed successfully at {target_cell}")
                            else:
                                action_error = result.get('error', 'Type failed')
                        else:
                            log_step(f"⚠️ [EXECUTOR] Could not find field {step_field} in vision")
                            action_error = f"Field {step_field} not found"
                    
                elif step_action == 'CLICK':
                    # Клик через human_click
                    log_step(f"👆 [EXECUTOR] human_click on {step_target}")
                    
                    # Найти кнопку в vision
                    await browser_service._inject_grid_overlay(page)
                    dom_data = await browser_service._collect_dom_clickables(page)
                    screenshot_b64 = await browser_service.capture_screenshot(session_id)
                    vision_elements = await browser_service._augment_with_vision(screenshot_b64, dom_data)
                    
                    target_cell = None
                    for el in vision_elements:
                        el_label = (el.get('label') or '').lower()
                        el_type = (el.get('type') or '').lower()
                        if step_target.lower() in el_label or (el_type == 'button' and not target_cell):
                            target_cell = el.get('cell')
                            break
                    
                    if target_cell:
                        result = await browser_service.click_cell(session_id, target_cell, human_like=True)
                        if result.get('success'):
                            action_executed = True
                            await asyncio.sleep(random.uniform(1.5, 3.0))  # wait for page reaction
                            log_step(f"✅ [EXECUTOR] Clicked successfully at {target_cell}")
                        else:
                            action_error = result.get('error', 'Click failed')
                    else:
                        log_step(f"⚠️ [EXECUTOR] Could not find button {step_target} in vision")
                        action_error = f"Button {step_target} not found"
                
                elif step_action == 'VERIFY_RESULT':
                    # Верификация не требует действия, только проверка
                    log_step(f"🔍 [EXECUTOR] Verification step (no action)")
                    action_executed = True
                    
                elif step_action == 'WAIT_USER':
                    # Остановка и ожидание оператора
                    log_step(f"⏸️ [EXECUTOR] WAIT_USER - stopping for operator")
                    agent_status = "WAITING_USER"
                    pending_user_prompt = step_target or "User input required"
                    # Сохраняем состояние
                    try:
                        storage = await page.context.storage_state()
                        with open(f"/tmp/waiting_state_{session_id}.json", 'w') as f:
                            import json
                            json.dump(storage, f)
                        log_step(f"✅ [EXECUTOR] State saved for operator")
                    except Exception as e:
                        log_step(f"⚠️ [EXECUTOR] Failed to save state: {e}")
                    break
                
                elif step_action == 'WAIT':
                    # Wait for specified milliseconds
                    wait_ms = int(step_target) if step_target else 1000
                    log_step(f"⏱️  [EXECUTOR] Waiting {wait_ms}ms")
                    await asyncio.sleep(wait_ms / 1000.0)
                    action_executed = True
                    
                else:
                    log_step(f"⚠️ [PLAN] Unknown action: {step_action}")
                    action_error = f"Unknown action {step_action}"
                    
            except Exception as e:
                log_step(f"❌ [EXECUTOR] Action failed: {str(e)}")
                action_error = str(e)
                import traceback
                traceback.print_exc()
            
            # Если не удалось выполнить действие из-за ошибки - переходим к retry
            if action_error and not action_executed:
                log_step(f"❌ [EXECUTOR] Action failed: {action_error}")
                # Обработка ошибки на следующем шаге (валидатор решит)
            
            # ============================================================
            # STEP 5: CAPTURE STATE AFTER ACTION (для валидации)
            # ============================================================
            screenshot_after = None
            vision_after = []
            
            if action_executed or action_error:
                try:
                    await asyncio.sleep(random.uniform(1.0, 2.0))  # wait for page update
                    page = browser_service.sessions[session_id]['page']
                    await browser_service._inject_grid_overlay(page)
                    dom_data_after = await browser_service._collect_dom_clickables(page)
                    screenshot_after = await browser_service.capture_screenshot(session_id)
                    vision_after = await browser_service._augment_with_vision(screenshot_after, dom_data_after)
                    log_step(f"📸 [VALIDATOR] Captured state AFTER action: {len(vision_after)} elements")
                except Exception as e:
                    log_step(f"⚠️ [VALIDATOR] Failed to capture AFTER state: {e}")
            
            # ============================================================
            # STEP 6: VALIDATE STEP (Florence-2 → fallback VLM)
            # ============================================================
            validation_result = None
            
            if action_executed and screenshot_after:
                log_step(f"🔍 [VALIDATOR] Validating step {current_step_id}")
                
                # PHASE 1: Try Florence-2 local validation (FAST, FREE)
                try:
                    from services.local_vision_service import local_vision_service
                    
                    # Florence-2 для поиска ошибок на экране
                    florence_loaded = local_vision_service.load_florence_model()
                    
                    if florence_loaded:
                        log_step("🔍 [VALIDATOR] Using Florence-2 (local)")
                        # TODO: Florence-2 full pipeline для детекции ошибок
                        # Пока что упрощённая логика
                        florence_validation = {"step_status": "ok", "confidence": 0.5}
                    else:
                        florence_validation = {"step_status": "unknown", "confidence": 0.0}
                        log_step("⚠️ [VALIDATOR] Florence-2 not available")
                except Exception as e:
                    log_step(f"⚠️ [VALIDATOR] Florence-2 failed: {e}")
                    florence_validation = {"step_status": "unknown", "confidence": 0.0}
                
                # PHASE 2: Fallback to external VLM if low confidence
                if florence_validation.get('confidence', 0) < 0.7:
                    log_step("🔍 [VALIDATOR] Low confidence, using external VLM fallback")
                    
                    # Формируем промпт для валидатора
                    validator_prompt = f"""Analyze this screenshot after executing: {step_action} on field '{step_field or step_target}'.

Expected result: Field should be filled / button clicked / page changed.

Check for:
1. Error messages (red text, "invalid", "already taken", "required")
2. Success indicators (page change, new form, confirmation)
3. Stuck state (nothing happened)

Return JSON:
{{
  "step_status": "ok" | "needs_fix_and_retry" | "waiting_user",
  "field_fix": {{"field": "first_name", "new_value": "John"}} (if needs fix),
  "reason": "explanation",
  "waiting_reason": "phone number required" (if waiting_user),
  "confidence": 0.0-1.0
}}

CRITICAL: Only use "waiting_user" for phone/SMS/2FA/captcha. NOT for simple validation errors."""
                    
                    try:
                        # Вызываем валидатор через supervisor (переиспользуем существующий сервис)
                        validation_result = await supervisor_service.next_step(
                            goal=validator_prompt,
                            history=[],
                            screenshot_base64=screenshot_after,
                            vision=vision_after,
                            available_data={},
                            model='qwen/qwen2.5-vl',
                            mode='validate'  # Специальный режим валидации
                        )
                        
                        log_step(f"✅ [VALIDATOR] External VLM: {validation_result.get('next_action', 'ok')}")
                        
                        # Преобразуем ответ supervisor в формат валидации
                        if validation_result.get('next_action') == 'ERROR':
                            step_status = "needs_fix_and_retry"
                            reason = validation_result.get('ask_user', 'Validation error')
                        elif validation_result.get('next_action') == 'WAIT':
                            step_status = "waiting_user"
                            reason = "User input required"
                        else:
                            step_status = "ok"
                            reason = "Step validated successfully"
                        
                        validation_result = {
                            "step_status": step_status,
                            "reason": reason,
                            "confidence": validation_result.get('confidence', 0.7)
                        }
                        
                    except Exception as e:
                        log_step(f"❌ [VALIDATOR] External VLM failed: {e}")
                        validation_result = {"step_status": "ok", "reason": "Validation unavailable, assuming ok", "confidence": 0.5}
                else:
                    validation_result = florence_validation
                    log_step(f"✅ [VALIDATOR] Florence-2 validated: {validation_result.get('step_status')}")
            else:
                # Нет действия или скриншота - пропускаем валидацию
                validation_result = {"step_status": "ok", "reason": "No validation needed", "confidence": 1.0}
            
            # ============================================================
            # STEP 7: PROCESS VALIDATION RESULT
            # ============================================================
            step_status = validation_result.get('step_status', 'ok')
            
            log_step(f"📊 [VALIDATOR] Result: {step_status} (confidence={validation_result.get('confidence', 0)})")
            
            if step_status == 'ok':
                # ✅ Шаг успешен - переходим к следующему
                log_step(f"✅ [PLAN] Step {current_step_id} PASSED, moving to next")
                
                # Find next step in plan
                if step_next:
                    current_step_id = step_next
                else:
                    # Automatically determine next step by order
                    current_step_index = next((i for i, s in enumerate(plan_steps) if s.get('id') == current_step_id), -1)
                    if current_step_index >= 0 and current_step_index + 1 < len(plan_steps):
                        current_step_id = plan_steps[current_step_index + 1].get('id')
                        log_step(f"📍 [PLAN] Auto-advancing to next step: {current_step_id}")
                    else:
                        current_step_id = 'done'
                        log_step(f"📍 [PLAN] No more steps, marking as done")
                
                step_retry_count = 0  # Reset retry counter
                
                if not current_step_id or current_step_id == 'done':
                    log_step("🎉 [PLAN] All steps completed!")
                    agent_status = "DONE"
                    break
                    
            elif step_status == 'needs_fix_and_retry':
                # 🔧 Автофикс и повтор шага
                log_step(f"🔧 [PLAN] Step {current_step_id} needs fix: {validation_result.get('reason')}")
                
                step_retry_count += 1
                if step_retry_count >= max_retries_per_step:
                    log_step(f"❌ [PLAN] Max retries ({max_retries_per_step}) reached for step {current_step_id}")
                    agent_status = "ERROR"
                    break
                
                # Попытка автофикса данных (например, имя без цифр)
                field_fix = validation_result.get('field_fix')
                if field_fix:
                    fix_field = field_fix.get('field')
                    fix_value = field_fix.get('new_value')
                    if fix_field and fix_value:
                        log_step(f"🔧 [AUTO-FIX] Updating {fix_field} = {fix_value}")
                        used_data[fix_field] = fix_value
                        data_bundle[fix_field] = fix_value
                
                # Применяем политику для генерации новых данных
                if step_data_key and policy.get('name_generation_hint'):
                    if 'name' in step_data_key.lower():
                        # Регенерируем имя согласно политике
                        if 'russian' in policy['name_generation_hint']:
                            russian_first_names = ['Иван', 'Александр', 'Дмитрий', 'Сергей', 'Андрей']
                            russian_last_names = ['Иванов', 'Петров', 'Сидоров', 'Смирнов', 'Кузнецов']
                            if 'first' in step_data_key.lower():
                                new_value = random.choice(russian_first_names)
                            elif 'last' in step_data_key.lower():
                                new_value = random.choice(russian_last_names)
                            else:
                                new_value = fake.first_name()
                        else:
                            # Без цифр
                            new_value = fake.first_name() if 'first' in step_data_key.lower() else fake.last_name()
                        
                        log_step(f"🔧 [AUTO-FIX] Regenerated {step_data_key} = {new_value} (policy: {policy.get('name_generation_hint')})")
                        used_data[step_data_key] = new_value
                        data_bundle[step_data_key] = new_value
                
                # НЕ меняем current_step_id - повторяем тот же шаг
                log_step(f"🔄 [PLAN] Retrying step {current_step_id} (attempt {step_retry_count}/{max_retries_per_step})")
                
            elif step_status == 'waiting_user':
                # ⏸️ КРИТИЧНО: Реально нужен оператор (телефон/SMS/2FA)
                reason = validation_result.get('waiting_reason') or validation_result.get('reason', 'User input required')
                log_step(f"⏸️ [PLAN] Step {current_step_id} requires operator: {reason}")
                
                # ПРОВЕРКА: это реально телефон/SMS/2FA или просто ошибка валидации?
                is_real_blocker = any(kw in reason.lower() for kw in ['phone', 'sms', '2fa', 'captcha', 'verification code'])
                
                if not is_real_blocker:
                    log_step(f"⚠️ [VALIDATOR] False WAITING_USER (не телефон/SMS), treating as needs_fix_and_retry")
                    # Переводим в retry вместо блокировки оператора
                    step_retry_count += 1
                    if step_retry_count >= max_retries_per_step:
                        agent_status = "ERROR"
                        break
                    continue
                
                # Реально нужен оператор
                agent_status = "WAITING_USER"
                pending_user_prompt = reason
                
                # Сохраняем состояние
                try:
                    page = browser_service.sessions[session_id]['page']
                    storage = await page.context.storage_state()
                    with open(f"/tmp/waiting_state_{session_id}.json", 'w') as f:
                        import json
                        json.dump(storage, f)
                    log_step(f"✅ [WAITING_USER] State saved: {reason}")
                except Exception as e:
                    log_step(f"⚠️ [WAITING_USER] Failed to save state: {e}")
                
                break
            
            else:
                log_step(f"⚠️ [VALIDATOR] Unknown status: {step_status}, treating as ok")
                current_step_id = step_next
            
            # ============================================================
            # STEP 8: UPDATE OBSERVATION FOR UI
            # ============================================================
            last_observation = {
                "screenshot_base64": screenshot_after or screenshot_before,
                "screenshot_id": f"step_{step_count}",
                "vision": vision_after or [],
                "url": current_url,
                "step": step_count,
                "action": step_action,
                "validation": validation_result,
                "grid": {"rows": browser_service.grid_rows, "cols": browser_service.grid_cols},
                "status": agent_status
            }
            
            await asyncio.sleep(0.5)
        
        if step_count >= max_steps:
            log_step("⚠️  Max steps reached")
            agent_status = "ERROR"
        
        log_step("🏁 Execution finished")
        
        # ВАЖНО: Сообщаем пользователю какие данные были использованы
        used_data_summary = []
        for key, value in data_bundle.items():
            if value:
                used_data_summary.append(f"{key}: {value}")
        
        if used_data_summary:
            log_step(f"📋 [SUMMARY] Used data ({data_source}):")
            for item in used_data_summary:
                log_step(f"  • {item}")
        
        return {
            "status": agent_status,
            "job_id": job_id,
            "session_id": current_session_id,
            "steps_executed": step_count,
            "head_analysis": current_analysis,
            "used_data": {
                "source": data_source,
                "data": data_bundle
            }
        }
        
    except Exception as e:
        logger.error(f"exec error: {e}")
        agent_status = "ERROR"
        log_step(f"❌ Error: {str(e)}", status="fail")
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/adjust')
async def adjust(req: AdjustRequest):
    """
    Live operator override - изменение политики автоматизации на лету.
    Не останавливает цикл, обновляет policy для следующих шагов.
    """
    try:
        global current_plan, override_buffer, policy
        
        if current_plan is None:
            raise HTTPException(status_code=400, detail="No active automation to adjust")
        
        # Добавляем в буфер для обработки в цикле
        override_buffer.append(req.message)
        
        # Логируем в execution_logs
        log_step(f"[OVERRIDE] {req.message}", status="info")
        
        # Простейший парсинг политики из текста
        # Примеры: "имя без цифр", "русские имена", "не вводи телефон сам"
        msg_lower = req.message.lower()
        
        if "без цифр" in msg_lower or "no digits" in msg_lower:
            policy['name_generation_hint'] = "real human name without digits"
            log_step("[POLICY] Updated: name_generation_hint = no digits")
        
        if "русск" in msg_lower or "russian" in msg_lower:
            policy['name_generation_hint'] = "russian human name"
            log_step("[POLICY] Updated: name_generation_hint = russian")
        
        if "не вводи телефон" in msg_lower or "stop before phone" in msg_lower:
            policy['stop_before_phone'] = True
            log_step("[POLICY] Updated: stop_before_phone = true")
        
        if "ждать" in msg_lower or "wait for me" in msg_lower:
            policy['wait_before_action'] = True
            log_step("[POLICY] Updated: wait_before_action = true")
        
        # Сохраняем в plan hints для истории
        hint = {"ts": datetime.now().isoformat(), "message": req.message}
        current_plan.setdefault('hints', []).append(hint)
        
        return {
            "ok": True, 
            "message": "Override applied",
            "policy": policy,
            "buffer_size": len(override_buffer)
        }
    except Exception as e:
        logger.error(f"adjust error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/autonomous-status')
async def get_autonomous_status():
    """Get autonomous agent status and metrics"""
    return {
        "agent_state": autonomous_agent.state.value if autonomous_agent.state else "idle",
        "task_id": autonomous_agent.task_id,
        "current_goal": autonomous_agent.current_goal,
        "session_id": autonomous_agent.session_id,
        "resources": autonomous_agent.resources,
        "metrics": autonomous_agent.metrics,
        "execution_history": autonomous_agent.execution_history[-10:],  # Last 10 steps
        "current_step": autonomous_agent.current_step_index,
        "total_steps": len(autonomous_agent.current_plan.get("steps", [])) if autonomous_agent.current_plan else 0,
        "stuck_count": autonomous_agent.stuck_count,
        "runtime_seconds": (time.time() - autonomous_agent.start_time) if autonomous_agent.start_time else 0
    }

@router.get('/log')
async def get_log():
    return {
        "task": current_task,
        "status": agent_status,
        "logs": execution_logs,
        "observation": last_observation,
        "session_id": current_session_id,
        "plan": current_plan,
        "current_step_id": current_step_id,  # NEW: текущий шаг
        "policy": policy,  # NEW: текущая политика
        "data_bundle": data_bundle,  # NEW: используемые данные
        "ask_user": pending_user_prompt  # NEW: что нужно от оператора
    }


@router.post('/automation-chat')
async def automation_chat(req: Dict[str, Any]):
    """
    Chat endpoint для общения с automation brain напрямую.
    Используется когда пользователь в automation mode и пишет сообщения.
    
    Request:
        {
            "message": "Подожди, заполни другой email",
            "context": "optional context from main chat"
        }
    
    Response:
        {
            "reply": "Понял, какой email использовать?",
            "action": "pause" | "resume" | "adjust" | None
        }
    """
    global automation_chat_history, agent_status, current_plan
    
    try:
        user_message = req.get('message', '')
        context_from_main = req.get('context')
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message required")
        
        # Добавляем в историю automation chat
        automation_chat_history.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat(),
            "context_from_main": context_from_main
        })
        
        # Ограничиваем историю (последние 20 сообщений)
        if len(automation_chat_history) > 20:
            automation_chat_history = automation_chat_history[-20:]
        
        # Формируем промпт для automation brain
        # TODO: Интегрировать с OpenRouter LLM для умных ответов
        # system_prompt = """..."""
        
        user_prompt = f"Пользователь: {user_message}"
        if context_from_main:
            user_prompt += f"\n\nКонтекст от главного чата: {context_from_main}"
        
        # Вызываем LLM для ответа
        # Временно - простой ответ, потом добавим полноценный LLM
        reply = f"Понял ваше сообщение: '{user_message}'. "
        action = None
        
        if any(kw in user_message.lower() for kw in ['подожди', 'стоп', 'pause', 'остановись']):
            reply += "Ставлю на паузу."
            action = "pause"
            agent_status = "PAUSED"
        elif any(kw in user_message.lower() for kw in ['продолжай', 'resume', 'дальше']):
            reply += "Продолжаю выполнение."
            action = "resume"
            agent_status = "ACTIVE"
        elif any(kw in user_message.lower() for kw in ['заполни', 'используй', 'измени', 'поменяй']):
            reply += "Корректирую данные."
            action = "adjust"
        
        # Добавляем ответ в историю
        automation_chat_history.append({
            "role": "assistant",
            "content": reply,
            "timestamp": datetime.now().isoformat(),
            "action": action
        })
        
        log_step(f"💬 [AUTOMATION CHAT] User: {user_message}")
        log_step(f"💬 [AUTOMATION CHAT] Brain: {reply}")
        
        return {
            "reply": reply,
            "action": action,
            "status": agent_status
        }
        
    except Exception as e:
        logger.error(f"automation_chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/automation-chat/history')
async def get_automation_chat_history():
    """Получить историю automation chat"""
    return {
        "history": automation_chat_history,
        "status": agent_status
    }

