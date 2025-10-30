from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import hashlib
from services.browser_automation_service import browser_service
from services.visual_validator_service import visual_validator_service
from services.scene_builder_service import scene_builder_service
from services.planner_service import planner_service
from services.cognitive_services import awareness_service, env_check_service, recon_service, inventory_service
from services.verifier_service import verifier_service, recovery_service
from services.antibot_guard_service import antibot_guard
from services.selftest_service import selftest_service

router = APIRouter(prefix="/api/automation", tags=["automation"])
logger = logging.getLogger(__name__)

# ============= Request Models =============

class CreateSessionRequest(BaseModel):
    session_id: str
    use_proxy: bool = False

class NavigateRequest(BaseModel):
    session_id: str
    url: str

class ClickCellRequest(BaseModel):
    session_id: str
    cell: str
    click_type: str = 'single'
    humanize: bool = True

class TypeAtCellRequest(BaseModel):
    session_id: str
    cell: str
    text: str

class HoldDragRequest(BaseModel):
    session_id: str
    from_cell: str
    to_cell: str
    speed: Optional[float] = 1.0
    humanize: bool = True

class ScreenshotRequest(BaseModel):
    session_id: str

class ClickRequest(BaseModel):
    session_id: str
    selector: str

class TypeRequest(BaseModel):
    session_id: str
    selector: str
    text: str

class WaitRequest(BaseModel):
    session_id: str
    selector: str
    timeout: int = 10000

class FindElementsRequest(BaseModel):
    session_id: str
    description: str

class SmartTypeRequest(BaseModel):
    session_id: str
    description: str
    text: str

class SmartClickRequest(BaseModel):
    session_id: str
    target_hint: str

class SmartTypeRequestNew(BaseModel):
    session_id: str
    target_hint: str
    text: str

class ValidateNavigationRequest(BaseModel):
    screenshot: str
    expectedUrl: str
    currentUrl: str
    pageTitle: str
    description: str

class GridSetRequest(BaseModel):
    rows: int
    cols: int

class SmokeCheckRequest(BaseModel):
    url: Optional[str] = None
    use_proxy: bool = False

@router.get("/screenshot/{session_id}/full")
async def get_screenshot_full(session_id: str):
    try:
        if session_id not in browser_service.sessions:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        page = browser_service.sessions[session_id]['page']
        await browser_service._inject_grid_overlay(page)
        dom_data = await browser_service._collect_dom_clickables(page)
        screenshot_b64 = await browser_service.capture_screenshot(session_id)
        vision = await browser_service._augment_with_vision(screenshot_b64, dom_data)
        sid = hashlib.md5(screenshot_b64.encode('utf-8')).hexdigest()
        return {
            "screenshot_base64": screenshot_b64,
            "screenshot_id": sid,
            "grid": {"rows": browser_service.grid_rows, "cols": browser_service.grid_cols},
            "vision": vision,
            "viewport": {"width": dom_data.get('vw', 1280), "height": dom_data.get('vh', 800)},
            "status": "idle"
        }
    except Exception as e:
        logger.error(f"Error capturing screenshot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Endpoints =============

@router.post("/session/create")
async def create_session(request: CreateSessionRequest):
    """Create new browser automation session with optional proxy"""
    try:
        result = await browser_service.create_session(
            request.session_id,
            use_proxy=request.use_proxy
        )
        return result
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/navigate")
async def navigate(request: NavigateRequest):
    """Navigate to URL"""
    try:
        # Check if session exists, recreate if needed
        if request.session_id not in browser_service.sessions:
            logger.warning(f"Session {request.session_id} not found, recreating...")
            await browser_service.create_session(request.session_id, use_proxy=False)
        
        result = await browser_service.navigate(request.session_id, request.url)
        return result
    except Exception as e:
        logger.error(f"Error navigating: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/click")
async def click_element(request: ClickRequest):
    """Click element by selector"""
    try:
        # Check if session exists
        if request.session_id not in browser_service.sessions:
            raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found. Create session first.")
        
        result = await browser_service.click_element(request.session_id, request.selector)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clicking: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/type")
async def type_text(request: TypeRequest):
    """Type text into element by selector"""
    try:
        result = await browser_service.type_text(request.session_id, request.selector, request.text)
        return result
    except Exception as e:
        logger.error(f"Error typing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/type-text")
async def smart_type_text(request: SmartTypeRequest):
    """
    Smart type: Use vision model to find element by description, then type text
    Example: description="email field", text="user@example.com"
    """
    try:
        # Find element using vision
        elements = await browser_service.find_elements_with_vision(
            request.session_id,
            request.description
        )
        
        if not elements:
            raise HTTPException(status_code=404, detail=f"Element '{request.description}' not found")
        
        # Click and type into the first (most confident) element
        best_element = elements[0]
        box = best_element['box']
        
        # Click at center of bounding box to focus
        center_x = box['x'] + box['width'] / 2
        center_y = box['y'] + box['height'] / 2
        
        page = browser_service.sessions[request.session_id]['page']
        await page.mouse.click(center_x, center_y)
        await page.wait_for_timeout(500)
        
        # Type the text
        await page.keyboard.type(request.text)
        await page.wait_for_timeout(500)
        
        screenshot = await browser_service.capture_screenshot(request.session_id)
        sid = hashlib.md5(screenshot.encode('utf-8')).hexdigest() if screenshot else None
        
        return {
            "success": True,
            "typed_into": best_element,
            "text": request.text,
            "screenshot": screenshot,
            "screenshot_id": sid,
            "box": box
        }
        
    except Exception as e:
        logger.error(f"Error in smart type: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/screenshot")
async def screenshot_query(session_id: str):
    try:
        # get screenshot + dom clickables and vision mapping
        if session_id not in browser_service.sessions:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        page = browser_service.sessions[session_id]['page']
        # ensure overlay
        await browser_service._inject_grid_overlay(page)
        dom_data = await browser_service._collect_dom_clickables(page)
        screenshot_b64 = await browser_service.capture_screenshot(session_id)
        vision = await browser_service._augment_with_vision(screenshot_b64, dom_data)
        sid = hashlib.md5(screenshot_b64.encode('utf-8')).hexdigest()
        return {
            "screenshot_base64": screenshot_b64,
            "screenshot_id": sid,
            "grid": {"rows": browser_service.grid_rows, "cols": browser_service.grid_cols},
            "vision": vision,
            "viewport": {"width": dom_data.get('vw', 1280), "height": dom_data.get('vh', 800)},
            "status": "idle"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/click-cell")
async def click_cell(req: ClickCellRequest):
    try:
        if req.session_id not in browser_service.sessions:
            raise HTTPException(status_code=404, detail=f"Session {req.session_id} not found")
        session = browser_service.sessions[req.session_id]
        page = session['page']
        await browser_service._inject_grid_overlay(page)
        # compute coordinates
        dom_data = await browser_service._collect_dom_clickables(page)
        vw, vh = dom_data.get('vw', 1280), dom_data.get('vh', 800)
        from services.grid_service import GridConfig
        grid = GridConfig(rows=browser_service.grid_rows, cols=browser_service.grid_cols)
        x, y = grid.cell_to_xy(req.cell, vw, vh)
        # human-like move+click
        from services.anti_detect import HumanBehaviorSimulator
        await HumanBehaviorSimulator.human_click(page, x, y)
        screenshot_b64 = await browser_service.capture_screenshot(req.session_id)
        vision = await browser_service._augment_with_vision(screenshot_b64, dom_data)
        sid = hashlib.md5(screenshot_b64.encode('utf-8')).hexdigest()
        return {
            "screenshot_base64": screenshot_b64,
            "screenshot_id": sid,
            "grid": {"rows": browser_service.grid_rows, "cols": browser_service.grid_cols},
            "vision": vision,
            "viewport": {"width": dom_data.get('vw', 1280), "height": dom_data.get('vh', 800)},
            "status": "idle",
            "dom_event": {"type": "click", "x": x, "y": y, "cell": req.cell}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/type-at-cell")
async def type_at_cell(req: TypeAtCellRequest):
    try:
        if req.session_id not in browser_service.sessions:
            raise HTTPException(status_code=404, detail=f"Session {req.session_id} not found")
        session = browser_service.sessions[req.session_id]
        page = session['page']
        await browser_service._inject_grid_overlay(page)
        dom_data = await browser_service._collect_dom_clickables(page)
        vw, vh = dom_data.get('vw', 1280), dom_data.get('vh', 800)
        from services.grid_service import GridConfig
        grid = GridConfig(rows=browser_service.grid_rows, cols=browser_service.grid_cols)
        x, y = grid.cell_to_xy(req.cell, vw, vh)
        from services.anti_detect import HumanBehaviorSimulator
        await HumanBehaviorSimulator.human_click(page, x, y)
        await HumanBehaviorSimulator.human_type(page, None, req.text)
        screenshot_b64 = await browser_service.capture_screenshot(req.session_id)
        vision = await browser_service._augment_with_vision(screenshot_b64, dom_data)
        sid = hashlib.md5(screenshot_b64.encode('utf-8')).hexdigest()
        return {
            "screenshot_base64": screenshot_b64,
            "screenshot_id": sid,
            "grid": {"rows": browser_service.grid_rows, "cols": browser_service.grid_cols},
            "vision": vision,
            "viewport": {"width": dom_data.get('vw', 1280), "height": dom_data.get('vh', 800)},
            "status": "idle",
            "dom_event": {"type": "type", "x": x, "y": y, "cell": req.cell, "text": req.text[:20]}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hold-drag")
async def hold_drag(req: HoldDragRequest):
    try:
        if req.session_id not in browser_service.sessions:
            raise HTTPException(status_code=404, detail=f"Session {req.session_id} not found")
        session = browser_service.sessions[req.session_id]
        page = session['page']
        await browser_service._inject_grid_overlay(page)
        dom_data = await browser_service._collect_dom_clickables(page)
        vw, vh = dom_data.get('vw', 1280), dom_data.get('vh', 800)
        from services.grid_service import GridConfig
        grid = GridConfig(rows=browser_service.grid_rows, cols=browser_service.grid_cols)
        sx, sy = grid.cell_to_xy(req.from_cell, vw, vh)
        ex, ey = grid.cell_to_xy(req.to_cell, vw, vh)
        from services.anti_detect import HumanBehaviorSimulator
        await HumanBehaviorSimulator.human_drag(page, sx, sy, ex, ey)
        screenshot_b64 = await browser_service.capture_screenshot(req.session_id)
        vision = await browser_service._augment_with_vision(screenshot_b64, dom_data)
        sid = hashlib.md5(screenshot_b64.encode('utf-8')).hexdigest()
        return {
            "screenshot_base64": screenshot_b64,
            "screenshot_id": sid,
            "grid": {"rows": browser_service.grid_rows, "cols": browser_service.grid_cols},
            "vision": vision,
            "viewport": {"width": dom_data.get('vw', 1280), "height": dom_data.get('vh', 800)},
            "status": "idle",
            "dom_event": {"type": "drag", "from": req.from_cell, "to": req.to_cell}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ScrollRequest(BaseModel):
    session_id: str
    dx: int = 0
    dy: int = 400

class WaitMsRequest(BaseModel):
    ms: int = 500

@router.post("/scroll")
async def do_scroll(req: ScrollRequest):
    try:
        result = await browser_service.scroll(req.session_id, req.dx, req.dy)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/wait")
async def do_wait(req: WaitMsRequest):
    try:
        await browser_service.wait(req.ms)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/wait-for")
async def wait_for_element(request: WaitRequest):
    """Wait for element to appear"""
    try:
        result = await browser_service.wait_for_element(
            request.session_id,
            request.selector,
            request.timeout
        )
        return result
    except Exception as e:
        logger.error(f"Error waiting: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/screenshot/{session_id}")
async def get_screenshot_endpoint(session_id: str):
    """Get current page screenshot with vision data"""
    try:
        if session_id not in browser_service.sessions:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        page = browser_service.sessions[session_id]['page']
        await browser_service._inject_grid_overlay(page)
        dom_data = await browser_service._collect_dom_clickables(page)
        screenshot_b64 = await browser_service.capture_screenshot(session_id)
        vision = await browser_service._augment_with_vision(screenshot_b64, dom_data)
        sid = hashlib.md5(screenshot_b64.encode('utf-8')).hexdigest()
        
        return {
            "screenshot_base64": screenshot_b64,
            "screenshot_id": sid,
            "vision": vision,
            "viewport": {"width": dom_data.get('vw', 1280), "height": dom_data.get('vh', 800)},
            "grid": {"rows": browser_service.grid_rows, "cols": browser_service.grid_cols}
        }
    except Exception as e:
        logger.error(f"Error capturing screenshot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============= Utility: Grid density set =============
@router.post("/grid/set")
async def set_grid_density(req: GridSetRequest):
    try:
        rows = max(4, min(256, req.rows))
        cols = max(4, min(256, req.cols))
        browser_service.grid_rows = rows
        browser_service.grid_cols = cols
        return {"success": True, "rows": rows, "cols": cols}
    except Exception as e:
        logger.error(f"Error setting grid: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Small helper to get grid density
@router.get("/grid")
async def get_grid():
    try:
        return {"rows": browser_service.grid_rows, "cols": browser_service.grid_cols}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= Supervisor (omitted for brevity) =============
from services.supervisor_service import supervisor_service
from pydantic import BaseModel
from typing import List

class NextStepRequest(BaseModel):
    goal: str
    history: List[Dict[str, Any]] = []
    screenshot_base64: str
    vision: List[Dict[str, Any]] = []
    model: Optional[str] = None

@router.post("/brain/next-step")
async def brain_next_step(req: NextStepRequest):
    try:
        result = await supervisor_service.next_step(
            goal=req.goal,
            history=req.history,
            screenshot_base64=req.screenshot_base64,
            vision=req.vision,
            model=req.model or 'qwen/qwen2.5-vl'
        )
        return result
    except Exception as e:
        logger.error(f"Error getting next step: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_screenshot(session_id: str):
    """Get current page screenshot"""
    try:
        result = await browser_service.capture_screenshot(session_id)
        return {"screenshot": result}
    except Exception as e:
        logger.error(f"Error capturing screenshot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/page-info/{session_id}")
async def get_page_info(session_id: str):
    """Get current page information"""
    try:
        result = await browser_service.get_page_info(session_id)
        return result
    except Exception as e:
        logger.error(f"Error getting page info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/find-elements")
async def find_elements(request: FindElementsRequest):
    """Find elements using LOCAL vision model (Florence-2) - NO API COSTS"""
    try:
        result = await browser_service.find_elements_with_vision(
            request.session_id,
            request.description
        )
        return {"elements": result}
    except Exception as e:
        logger.error(f"Error finding elements: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/smart-click-legacy")
async def smart_click(request: FindElementsRequest):
    try:
        elements = await browser_service.find_elements_with_vision(
            request.session_id,
            request.description
        )
        if not elements:
            raise HTTPException(status_code=404, detail=f"Element '{request.description}' not found")
        best_element = elements[0]
        box = best_element['box']
        center_x = box['x'] + box['width'] / 2
        center_y = box['y'] + box['height'] / 2
        page = browser_service.sessions[request.session_id]['page']
        await page.mouse.click(center_x, center_y)
        await page.wait_for_timeout(1000)
        screenshot = await browser_service.capture_screenshot(request.session_id)
        sid = hashlib.md5(screenshot.encode('utf-8')).hexdigest() if screenshot else None
        return {"success": True, "clicked_element": best_element, "screenshot": screenshot, "screenshot_id": sid, "box": box}
    except Exception as e:
        logger.error(f"Error in smart click: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/smoke-check")
async def smoke_check(req: SmokeCheckRequest):
    """Create a fresh session, navigate to URL, and return a screenshot + grid + vision + screenshot_id in one atomic call."""
    try:
        sid = f"smoke-{id(req)}-{int(__import__('time').time()*1000)}"
        await browser_service.create_session(sid, use_proxy=req.use_proxy)
        url = req.url or "https://example.com"
        nav = await browser_service.navigate(sid, url)
        page = browser_service.sessions[sid]['page']
        await browser_service._inject_grid_overlay(page)
        dom_data = await browser_service._collect_dom_clickables(page)
        screenshot_b64 = await browser_service.capture_screenshot(sid)
        vision = await browser_service._augment_with_vision(screenshot_b64, dom_data)
        shot_id = hashlib.md5(screenshot_b64.encode('utf-8')).hexdigest()
        return {
            "success": True,
            "session_id": sid,
            "url": nav.get('url', url),
            "title": nav.get('title'),
            "screenshot_base64": screenshot_b64,
            "screenshot_id": shot_id,
            "grid": {"rows": browser_service.grid_rows, "cols": browser_service.grid_cols},
            "viewport": {"width": dom_data.get('vw', 1280), "height": dom_data.get('vh', 800)},
            "vision": vision
        }
    except Exception as e:
        logger.error(f"Smoke-check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= BLOCK 1: Scene Builder Endpoints =============

class SceneSnapshotRequest(BaseModel):
    session_id: str

@router.post("/scene/snapshot")
async def scene_snapshot(req: SceneSnapshotRequest):
    """
    Build Scene JSON from current page state
    Returns: Scene JSON with viewport, url, http, antibot, elements[], hints
    """
    try:
        if req.session_id not in browser_service.sessions:
            raise HTTPException(status_code=404, detail=f"Session {req.session_id} not found")
        
        page = browser_service.sessions[req.session_id]['page']
        
        # Inject grid overlay
        await browser_service._inject_grid_overlay(page)
        
        # Collect DOM clickables
        dom_data = await browser_service._collect_dom_clickables(page)
        
        # Get screenshot for vision
        screenshot_b64 = await browser_service.capture_screenshot(req.session_id)
        
        # Augment with vision
        vision = await browser_service._augment_with_vision(screenshot_b64, dom_data)
        
        # Build Scene JSON
        scene = await scene_builder_service.build_scene(
            page=page,
            dom_data=dom_data,
            vision_elements=vision,
            session_id=req.session_id
        )
        
        logger.info(f"📸 Scene snapshot: {len(scene['elements'])} elements, antibot={scene['antibot']['present']}")
        
        return {
            "success": True,
            "scene": scene,
            "screenshot_base64": screenshot_b64,
            "screenshot_id": hashlib.md5(screenshot_b64.encode('utf-8')).hexdigest()
        }
        
    except Exception as e:
        logger.error(f"Scene snapshot error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= BLOCK 2: Planner (UIG) Endpoints =============

class PlanDecideRequest(BaseModel):
    session_id: str
    goal: Dict[str, Any]
    scene: Optional[Dict[str, Any]] = None

@router.post("/plan/decide")
async def plan_decide(req: PlanDecideRequest):
    """
    Generate multi-path plan (A/B/C) from goal + scene
    Uses Qwen2.5-Instruct for planning
    """
    try:
        # Get scene if not provided
        scene = req.scene
        if not scene:
            if req.session_id not in browser_service.sessions:
                raise HTTPException(status_code=404, detail=f"Session {req.session_id} not found")
            
            page = browser_service.sessions[req.session_id]['page']
            await browser_service._inject_grid_overlay(page)
            dom_data = await browser_service._collect_dom_clickables(page)
            screenshot_b64 = await browser_service.capture_screenshot(req.session_id)
            vision = await browser_service._augment_with_vision(screenshot_b64, dom_data)
            scene = await scene_builder_service.build_scene(page, dom_data, vision, req.session_id)
        
        # Generate plan
        result = await planner_service.decide_plan(
            goal=req.goal,
            scene=scene
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Planning failed'))
        
        logger.info(f"📋 Plan generated: {len(result['plan'].get('candidates', []))} candidates")
        
        return {
            "success": True,
            "plan": result['plan'],
            "usage": result.get('usage', {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Plan decide error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= BLOCK 3: Cognitive Loop Endpoints =============

class AwarenessRequest(BaseModel):
    raw_goal: str
    site: str
    constraints: Optional[Dict[str, Any]] = None

class EnvCheckRequest(BaseModel):
    session_id: str

class ReconRequest(BaseModel):
    session_id: str
    scene: Optional[Dict[str, Any]] = None

class InventoryRequest(BaseModel):
    goal: Dict[str, Any]
    chosen_plan: Dict[str, Any]
    available_resources: Optional[Dict[str, Any]] = None

@router.post("/awareness/think")
async def awareness_think(req: AwarenessRequest):
    """Awareness: Normalize goal and propose routes"""
    try:
        result = await awareness_service.think(
            raw_goal=req.raw_goal,
            site=req.site,
            constraints=req.constraints
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error'))
        
        return {
            "success": True,
            "result": result['result']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Awareness error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/env/check")
async def env_check(req: EnvCheckRequest):
    """Environment Check: Classify current state"""
    try:
        if req.session_id not in browser_service.sessions:
            raise HTTPException(status_code=404, detail=f"Session {req.session_id} not found")
        
        page = browser_service.sessions[req.session_id]['page']
        url = page.url
        
        # Get HTTP status (simplified)
        http_status = 200
        
        # Get antibot info from scene
        dom_data = await browser_service._collect_dom_clickables(page)
        screenshot_b64 = await browser_service.capture_screenshot(req.session_id)
        vision = await browser_service._augment_with_vision(screenshot_b64, dom_data)
        scene = await scene_builder_service.build_scene(page, dom_data, vision, req.session_id)
        
        result = await env_check_service.check(
            session_id=req.session_id,
            url=url,
            http_status=http_status,
            antibot=scene.get('antibot', {})
        )
        
        return {
            "success": True,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Env check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recon/scan")
async def recon_scan(req: ReconRequest):
    """Recon: Identify entry points"""
    try:
        scene = req.scene
        if not scene:
            if req.session_id not in browser_service.sessions:
                raise HTTPException(status_code=404, detail=f"Session {req.session_id} not found")
            
            page = browser_service.sessions[req.session_id]['page']
            dom_data = await browser_service._collect_dom_clickables(page)
            screenshot_b64 = await browser_service.capture_screenshot(req.session_id)
            vision = await browser_service._augment_with_vision(screenshot_b64, dom_data)
            scene = await scene_builder_service.build_scene(page, dom_data, vision, req.session_id)
        
        result = await recon_service.scan(scene)
        
        return {
            "success": True,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recon error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/inventory/check")
async def inventory_check(req: InventoryRequest):
    """Inventory Gate: Check resource availability"""
    try:
        result = await inventory_service.check(
            goal=req.goal,
            plan=req.chosen_plan,
            available_resources=req.available_resources
        )
        
        return {
            "success": True,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Inventory check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= BLOCK 4: Verifier + Recovery Endpoints =============

class VerifyResultRequest(BaseModel):
    prevScene: Dict[str, Any]
    currScene: Dict[str, Any]
    lastAction: Dict[str, Any]
    goal: Dict[str, Any]

class RepairPlanRequest(BaseModel):
    scene: Dict[str, Any]
    remediation: str
    goal: Dict[str, Any]

@router.post("/result/verify")
async def result_verify(req: VerifyResultRequest):
    """Verify action results by comparing scenes"""
    try:
        result = await verifier_service.verify(
            prev_scene=req.prevScene,
            curr_scene=req.currScene,
            last_action=req.lastAction,
            goal=req.goal
        )
        
        return {
            "success": True,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Verify error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/repair/plan")
async def repair_plan(req: RepairPlanRequest):
    """Generate recovery steps from remediation"""
    try:
        result = await recovery_service.plan_recovery(
            scene=req.scene,
            remediation=req.remediation,
            goal=req.goal
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Recovery planning failed'))
        
        return {
            "success": True,
            "steps": result['steps']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Repair plan error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============= BLOCK 5: AntiBot Guard Endpoints =============

class AntiBotEvalRequest(BaseModel):
    scene: Dict[str, Any]
    history: List[Dict[str, Any]] = []

class ProfileSwitchRequest(BaseModel):
    session_id: str
    profile: str

@router.post("/antibot/eval")
async def antibot_eval(req: AntiBotEvalRequest):
    """Evaluate antibot policy"""
    try:
        result = await antibot_guard.eval_policy(
            scene=req.scene,
            history=req.history
        )
        
        return {
            "success": True,
            "decision": result['decision']
        }
        
    except Exception as e:
        logger.error(f"AntiBot eval error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/antibot/profile/switch")
async def antibot_profile_switch(req: ProfileSwitchRequest):
    """Switch browser profile"""
    try:
        result = await antibot_guard.switch_profile(
            browser_service=browser_service,
            session_id=req.session_id,
            profile_name=req.profile
        )
        
        if not result.get('ok'):
            raise HTTPException(status_code=500, detail=result.get('error'))
        
        return {
            "ok": True,
            "profile": result['profile'],
            "message": result['message']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile switch error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/antibot/profiles")
async def antibot_profiles():
    """Get available profiles"""
    try:
        profiles = antibot_guard.get_available_profiles()
        return {
            "profiles": profiles
        }
    except Exception as e:
        logger.error(f"Get profiles error: {str(e)}")



