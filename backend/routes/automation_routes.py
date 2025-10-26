from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from services.browser_automation_service import browser_service

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
async def smart_type_text(request: FindElementsRequest):
    """
    Smart type: Use vision model to find element by description, then type text
    Example: description="email field", text="user@example.com"
    """
    try:
        # Parse request body for text field
        from pydantic import BaseModel
        class SmartTypeRequest(BaseModel):
            session_id: str
            description: str
            text: str
        
        # Re-parse with correct model
        smart_req = SmartTypeRequest(**request.dict(), text=request.dict().get('text', ''))
        
        # Find element using vision
        elements = await browser_service.find_elements_with_vision(
            smart_req.session_id,
            smart_req.description
        )
        
        if not elements:
            raise HTTPException(status_code=404, detail=f"Element '{smart_req.description}' not found")
        
        # Click and type into the first (most confident) element
        best_element = elements[0]
        box = best_element['box']
        
        # Click at center of bounding box to focus
        center_x = box['x'] + box['width'] / 2
        center_y = box['y'] + box['height'] / 2
        
        page = browser_service.sessions[smart_req.session_id]['page']
        await page.mouse.click(center_x, center_y)
        await page.wait_for_timeout(500)
        
        # Type the text
        await page.keyboard.type(smart_req.text)
        await page.wait_for_timeout(500)
        
        screenshot = await browser_service.capture_screenshot(smart_req.session_id)
        
        return {
            "success": True,
            "typed_into": best_element,
            "text": smart_req.text,
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
            "screenshot": screenshot
        }
        
    except Exception as e:
        logger.error(f"Error in smart click: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def close_session(session_id: str):
    """Close browser session"""
    try:
        await browser_service.close_session(session_id)
        return {"message": "Session closed successfully"}
    except Exception as e:
        logger.error(f"Error closing session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
