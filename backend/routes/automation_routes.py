from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from services.browser_automation_service import browser_service
from services.visual_validator_service import visual_validator_service

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
        return {
            "screenshot_base64": screenshot_b64,
            "grid": {"rows": browser_service.grid_rows, "cols": browser_service.grid_cols},
            "vision": vision,
            "status": "idle"
        }
    except Exception as e:
        logger.error(f"Error capturing screenshot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    pageTitle: str
    description: str


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
        
        return {
            "success": True,
            "typed_into": best_element,
            "text": request.text,
            "screenshot": screenshot,
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
        return {
            "screenshot_base64": screenshot_b64,
            "grid": {"rows": browser_service.grid_rows, "cols": browser_service.grid_cols},
            "vision": vision,
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
        return {
            "screenshot_base64": screenshot_b64,
            "grid": {"rows": browser_service.grid_rows, "cols": browser_service.grid_cols},
            "vision": vision,
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
        await HumanBehaviorSimulator.human_move(page, x, y)
        await page.mouse.click(x, y)
        await page.keyboard.type(req.text, delay=50)
        screenshot_b64 = await browser_service.capture_screenshot(req.session_id)
        vision = await browser_service._augment_with_vision(screenshot_b64, dom_data)
        return {
            "screenshot_base64": screenshot_b64,
            "grid": {"rows": browser_service.grid_rows, "cols": browser_service.grid_cols},
            "vision": vision,
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
        return {
            "screenshot_base64": screenshot_b64,
            "grid": {"rows": browser_service.grid_rows, "cols": browser_service.grid_cols},
            "vision": vision,
            "status": "idle",
            "dom_event": {"type": "drag", "from": req.from_cell, "to": req.to_cell}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/wait")
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

# ============= Supervisor (Step Brain) =============
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


@router.post("/smart-click")
async def smart_click(request: FindElementsRequest):
    """
    Smart click: Use vision model to find element by description, then click it
    Example: description="login button" will find and click the login button
    """
    try:
        # Find element using vision
        elements = await browser_service.find_elements_with_vision(
            request.session_id,
            request.description
        )
        
        if not elements:
            raise HTTPException(status_code=404, detail=f"Element '{request.description}' not found")
        
        # Click the first (most confident) element
        best_element = elements[0]
        box = best_element['box']
        
        # Click at center of bounding box
        center_x = box['x'] + box['width'] / 2
        center_y = box['y'] + box['height'] / 2
        
        page = browser_service.sessions[request.session_id]['page']
        await page.mouse.click(center_x, center_y)
        await page.wait_for_timeout(1000)
        
        screenshot = await browser_service.capture_screenshot(request.session_id)
        
        return {
            "success": True,
            "clicked_element": best_element,
            "screenshot": screenshot,
            "box": box
        }
        
    except Exception as e:
        logger.error(f"Error in smart click: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/smart-click")
async def smart_click_endpoint(request: SmartClickRequest):
    """
    Smart click using vision model to find and click element by natural language description
    """
    try:
        result = await browser_service.smart_click(
            session_id=request.session_id,
            target_hint=request.target_hint
        )
        return result
        
    except Exception as e:
        logger.error(f"Error in smart click: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/smart-type")
async def smart_type_endpoint(request: SmartTypeRequestNew):
    """
    Smart type using vision model to find input field and type text
    """
    try:
        result = await browser_service.smart_type(
            session_id=request.session_id,
            target_hint=request.target_hint,
            text=request.text
        )
        return result
        
    except Exception as e:
        logger.error(f"Error in smart type: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/close")
async def close_session_post(request: CreateSessionRequest):
    """Close browser session (POST version for frontend compatibility)"""
    try:
        await browser_service.close_session(request.session_id)
        return {"message": "Session closed successfully"}
    except Exception as e:
        logger.error(f"Error closing session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-navigation")
async def validate_navigation(request: ValidateNavigationRequest):
    """Validate navigation success using vision API"""
    try:
        result = await visual_validator_service.validate_navigation(
            screenshot_base64=request.screenshot,
            expected_url=request.expectedUrl,
            current_url=request.currentUrl,
            page_title=request.pageTitle,
            description=request.description
        )
        return result
    except Exception as e:
        logger.error(f"Error validating navigation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def close_session(session_id: str):
    """Close browser session (DELETE version)"""
    try:
        await browser_service.close_session(session_id)
        return {"message": "Session closed successfully"}
    except Exception as e:
        logger.error(f"Error closing session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/captcha/solve")
async def solve_captcha(request: Dict[str, str]):
    """Manually trigger CAPTCHA detection and solving"""
    try:
        session_id = request.get('session_id')
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        result = await browser_service.detect_and_solve_captcha(session_id)
        return result
    except Exception as e:
        logger.error(f"Error solving CAPTCHA: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
