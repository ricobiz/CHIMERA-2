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

class NavigateRequest(BaseModel):
    session_id: str
    url: str

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


# ============= Endpoints =============

@router.post("/session/create")
async def create_session(request: CreateSessionRequest):
    """Create new browser automation session"""
    try:
        result = await browser_service.create_session(request.session_id)
        return result
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/navigate")
async def navigate(request: NavigateRequest):
    """Navigate to URL"""
    try:
        result = await browser_service.navigate(request.session_id, request.url)
        return result
    except Exception as e:
        logger.error(f"Error navigating: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/click")
async def click_element(request: ClickRequest):
    """Click element by selector"""
    try:
        result = await browser_service.click_element(request.session_id, request.selector)
        return result
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
