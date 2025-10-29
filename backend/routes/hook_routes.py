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
from services.form_filler_service import form_filler_service
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
        # PHASE 3: PLAN-BASED EXECUTION LOOP (NEW ARCHITECTURE)
        # ============================================================
        # Данные для использования в автоматизации
        used_data = data_bundle
        
        # Получаем план шагов
        plan_steps = current_plan.get('steps', [])
        if not plan_steps:
            log_step("⚠️ [PLAN] No steps in plan, using fallback mode")
            # Fallback на старую логику если плана нет
            # (оставляем это как safety net, но основной путь - план)
        
        log_step(f"📋 [PLAN] Total steps in plan: {len(plan_steps)}")
        
        # Счётчик попыток retry для текущего шага
        step_retry_count = 0
        max_retries_per_step = 3
        
        while agent_status == "ACTIVE" and current_step_id and step_count < max_steps:
            step_count += 1
            log_step(f"🔄 [CYCLE {step_count}/{max_steps}]")
            
            # 1. ИСПОЛНИТЕЛЬ: Проверяем загружена ли страница
            try:
                page = browser_service.sessions[session_id]['page']
                loading_status = await browser_service.is_page_loading(page)
                
                if loading_status.get('is_loading'):
                    reason = loading_status.get('reason')
                    log_step(f"⏳ [EXECUTOR] Page still loading: {reason}")
                    # Ждём загрузки
                    await browser_service.wait_for_page_ready(page, timeout_ms=5000)
                    log_step("✅ [EXECUTOR] Page loading complete")
            except Exception as e:
                log_step(f"⚠️ [EXECUTOR] Loading check failed: {str(e)}")
            
            # 2. ИСПОЛНИТЕЛЬ: Захватить состояние ДО действия (для верификации)
            try:
                page = browser_service.sessions[session_id]['page']
                current_url = page.url
                await browser_service._inject_grid_overlay(page)
                dom_data_before = await browser_service._collect_dom_clickables(page)
                screenshot_before = await browser_service.capture_screenshot(session_id)
                vision_before = await browser_service._augment_with_vision(screenshot_before, dom_data_before)
                
                # Статистика для логов
                num_elements_before = len(vision_before or [])
                log_step(f"📸 [EXECUTOR] State BEFORE action: URL={current_url}, Elements={num_elements_before}")
            except Exception as e:
                log_step(f"❌ [EXECUTOR] Failed to capture BEFORE state: {str(e)}")
                vision_before = []
                screenshot_before = None
                current_url = "about:blank"
                dom_data_before = {}
                num_elements_before = 0
            
            # 2. СПИННОЙ МОЗГ: Принять решение на основе плана и текущего состояния
            brain_context = {
                "goal": goal,
                "strategy": head_analysis['strategy'],
                "data_available": data_bundle,
                "plan_outline": head_analysis.get('plan_outline', ''),
                "current_url": current_url,
                "history": history[-10:]
            }
            
            brain_goal = (
                f"{goal}\n"
                f"Strategy: {brain_context['strategy']}\n"
                f"Current URL: {current_url}\n"
                f"Available data: {list(data_bundle.keys())}\n"
                f"Elements visible: {num_elements_before}"
            )
            
            # ОПТИМИЗАЦИЯ: Сначала пробуем БЕЗ скриншота (только текст селекторов)
            send_screenshot = False
            if step_count == 1:
                send_screenshot = True
            elif consecutive_waits >= 2:
                send_screenshot = True
                log_step("⚠️ Multiple WAITs - sending screenshot to help decision")
            # Проверяем есть ли INPUT поля без понятных labels (нужен визуал!)
            elif vision_before:
                unclear_inputs = [v for v in vision_before if v.get('type') in ['input', 'INPUT', 'textarea'] and (not v.get('label') or v.get('label') == 'INPUT' or len(v.get('label', '')) < 3)]
                if len(unclear_inputs) > 0:
                    send_screenshot = True
                    log_step(f"⚠️ Found {len(unclear_inputs)} INPUT fields without clear labels - sending screenshot for visual analysis")
            elif len(history) > 0:
                last_step = history[-1]
                # Если в прошлой итерации спинной мозг попросил визуал
                if last_step.get('needs_visual'):
                    send_screenshot = True
                # Если в прошлой итерации действие выполнилось но страница НЕ изменилась
                if last_step.get('page_changed') is False:
                    send_screenshot = True
                    log_step("⚠️ Previous action had NO EFFECT - sending screenshot for analysis")
            
            # 🤖 SMART FORM FILLER - автоматическое определение и заполнение форм
            # Если видим INPUT поля (>=2), пробуем автоматически заполнить
            form_detected = None
            if vision_before and len([v for v in vision_before if v.get('type', '').lower() in ['input', 'textarea']]) >= 2:
                form_detected = form_filler_service.analyze_form(vision_before, current_url or '')
                if form_detected and form_detected.get('confidence', 0) > 0.6:
                    log_step(f"📋 [SMART FORM] Detected {form_detected.get('form_type')} form with {len(form_detected.get('fields', []))} fields")
                    
                    # Генерируем действия заполнения
                    fill_actions = form_filler_service.generate_fill_actions(form_detected, used_data or {})
                    
                    if len(fill_actions) > 0:
                        log_step(f"✅ [SMART FORM] Auto-filling {len(fill_actions)} fields...")
                        
                        # Выполняем каждое действие заполнения
                        for idx, fill_action in enumerate(fill_actions):
                            action_type = fill_action.get('action')
                            cell = fill_action.get('cell')
                            text = fill_action.get('text')
                            
                            log_step(f"  {idx+1}/{len(fill_actions)}: {action_type} at {cell}" + (f" = {text[:20]}..." if text else ""))
                            
                            if action_type == 'TYPE_AT_CELL' and cell and text:
                                result = await browser_service.type_at_cell(session_id, cell, text, human_like=True)
                                if not result.get('success'):
                                    log_step(f"⚠️ Failed to type at {cell}: {result.get('error')}")
                                await asyncio.sleep(random.uniform(0.5, 1.5))
                            elif action_type == 'CLICK_CELL' and cell:
                                result = await browser_service.click_cell(session_id, cell, human_like=True)
                                if result.get('success'):
                                    log_step(f"✅ Clicked submit button at {cell}")
                                await asyncio.sleep(random.uniform(1.0, 2.0))
                        
                        # После заполнения формы - продолжаем цикл
                        step_count += 1
                        continue
            
            brain_result = await supervisor_service.next_step(
                goal=brain_goal,
                history=history,
                screenshot_base64=screenshot_before if send_screenshot else None,
                vision=vision_before or [],
                available_data=used_data,  # Передаём данные в Spinal Cord!
                model='qwen/qwen2.5-vl'
            )
            
            needs_visual = brain_result.get('needs_user_input') or brain_result.get('confidence', 1.0) < 0.5
            
            action = brain_result.get('next_action', 'WAIT')
            target_cell = brain_result.get('target_cell')
            text_value = brain_result.get('text')
            
            mode = "📸 VISUAL" if send_screenshot else "📝 TEXT-ONLY"
            log_step(f"{mode} | 🧠 [SPINAL CORD] Decision: {action} at {target_cell or 'N/A'}")
            
            # Защита от зацикливания на WAIT
            if action == 'WAIT':
                consecutive_waits += 1
                if consecutive_waits >= 3:
                    log_step(f"⚠️ [ANTI-LOOP] Too many WAITs ({consecutive_waits}), forcing SCROLL or DONE")
                    if len(vision_before or []) > 0:
                        # Есть элементы - пробуем скроллить
                        action = 'SCROLL'
                        brain_result['direction'] = 'down'
                        brain_result['amount'] = 400
                        consecutive_waits = 0
                    else:
                        # Нет элементов вообще - возможно задача завершена
                        action = 'DONE'
            else:
                consecutive_waits = 0
            
            log_step(f"🧠 [SPINAL CORD] Decision: {action} at {target_cell or 'N/A'}")
            
            # 3. ИСПОЛНИТЕЛЬ: Выполнить действие
            action_executed = False
            
            if action == 'CLICK_CELL':
                if not target_cell:
                    log_step("⚠️ [EXECUTOR] No target cell for CLICK_CELL")
                    continue
                log_step(f"👆 [EXECUTOR] Clicking {target_cell}")
                await browser_service.click_cell(session_id, target_cell)
                action_executed = True
                
            elif action == 'TYPE_AT_CELL':
                if not target_cell or not text_value:
                    log_step("⚠️ [EXECUTOR] Missing target or text for TYPE_AT_CELL")
                    continue
                log_step(f"⌨️  [EXECUTOR] Typing '{text_value}' at {target_cell}")
                await browser_service.type_at_cell(session_id, target_cell, text_value)
                action_executed = True
                
            elif action == 'NAVIGATE':
                url = brain_result.get('url', 'https://accounts.google.com/signup')
                log_step(f"🌐 [EXECUTOR] Navigating to {url}")
                await browser_service.navigate(session_id, url)
                action_executed = True
                await asyncio.sleep(3)  # Дать странице загрузиться
                
            elif action == 'SCROLL':
                direction = brain_result.get('direction', 'down')
                amount = brain_result.get('amount', 400)
                log_step(f"📜 [EXECUTOR] Scrolling {direction} by {amount}px")
                dy = amount if direction == 'down' else -amount
                await browser_service.scroll(session_id, 0, dy)
                action_executed = True
                
            elif action == 'WAIT':
                log_step("⏳ [EXECUTOR] Waiting...")
                await asyncio.sleep(2)
                action_executed = False  # WAIT не требует верификации
                
            elif action == 'DONE':
                log_step("✅ [SPINAL CORD] Task completed")
                agent_status = "IDLE"
                break
                
            elif action == 'ERROR':
                error_msg = brain_result.get('ask_user', 'Unknown error')
                log_step(f"❌ [SPINAL CORD] Error: {error_msg}")
                agent_status = "ERROR"
                break
                
            else:
                log_step(f"⚠️ [SPINAL CORD] Unknown action: {action}, treating as WAIT")
                await asyncio.sleep(1)
                action_executed = False
            
            # 4. ВЕРИФИКАЦИЯ: Проверяем изменилась ли страница после действия
            page_changed = False
            screenshot_after = None
            vision_after = []
            
            if action_executed:
                await asyncio.sleep(1.5)  # Дать время на обработку действия
                
                try:
                    page = browser_service.sessions[session_id]['page']
                    url_after = page.url
                    await browser_service._inject_grid_overlay(page)
                    dom_data_after = await browser_service._collect_dom_clickables(page)
                    screenshot_after = await browser_service.capture_screenshot(session_id)
                    vision_after = await browser_service._augment_with_vision(screenshot_after, dom_data_after)
                    
                    num_elements_after = len(vision_after or [])
                    
                    # Сравниваем состояния
                    selectors_before = set([el.get('cell') for el in vision_before if el.get('cell')])
                    selectors_after = set([el.get('cell') for el in vision_after if el.get('cell')])
                    url_changed = (url_after != current_url)
                    elements_changed = (selectors_before != selectors_after)
                    
                    page_changed = url_changed or elements_changed or (abs(num_elements_after - num_elements_before) > 2)
                    
                    if page_changed:
                        log_step(f"✅ [VERIFICATION] Page CHANGED: URL={url_changed}, Elements={elements_changed} ({num_elements_before}→{num_elements_after})")
                        # Отправляем ТЕКСТ новых селекторов в следующей итерации
                        consecutive_waits = 0
                    else:
                        log_step("⚠️ [VERIFICATION] NO CHANGE detected - will send screenshot to Brain for analysis")
                        # Отправляем СКРИНШОТ (до и после) в следующей итерации для анализа
                        needs_visual = True
                        consecutive_waits = 0
                        
                except Exception as e:
                    log_step(f"❌ [VERIFICATION] Failed: {str(e)}")
                    page_changed = False
            
            # 5. История для следующей итерации
            history.append({
                "step": step_count,
                "action": action,
                "target": target_cell,
                "text": text_value if action == 'TYPE_AT_CELL' else None,
                "result": "executed",
                "page_changed": page_changed if action_executed else None,
                "needs_visual": needs_visual  # Флаг для следующей итерации
            })
            
            last_observation = {
                "screenshot_base64": screenshot_after or screenshot_before,
                "vision": vision_after or vision_before or [],
                "url": current_url,
                "step": step_count,
                "action": action,
                "verification": {
                    "action_executed": action_executed,
                    "page_changed": page_changed if action_executed else None
                },
                "grid": {"rows": browser_service.grid_rows, "cols": browser_service.grid_cols}
            }
            
            await asyncio.sleep(1.5)
        
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

