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
    """Type text into element"""
    try:
        result = await browser_service.type_text(request.session_id, request.selector, request.text)
        return result
    except Exception as e:
        logger.error(f"Error typing: {str(e)}")
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
    """Find elements using vision model"""
    try:
        result = await browser_service.find_elements_with_vision(
            request.session_id,
            request.description
        )
        return {"elements": result}
    except Exception as e:
        logger.error(f"Error finding elements: {str(e)}")
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
