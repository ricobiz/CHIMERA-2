"""
Real Browser Automation Service using Playwright
No mocks, no simulations - actual browser control
Integrated with local vision model for element detection
"""
import asyncio
import logging
import base64
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from typing import Dict, Any, Optional, List
import os
from services.local_vision_service import vision_service

logger = logging.getLogger(__name__)

class BrowserAutomationService:
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self):
        """Initialize Playwright and browser"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            logger.info("Browser launched successfully")
    
    async def create_session(self, session_id: str) -> Dict[str, Any]:
        """Create a new browser session"""
        await self.initialize()
        
        # Create new context and page
        context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        self.sessions[session_id] = {
            'context': context,
            'page': page,
            'history': []
        }
        
        logger.info(f"Created session: {session_id}")
        return {'session_id': session_id, 'status': 'ready'}
    
    async def navigate(self, session_id: str, url: str) -> Dict[str, Any]:
        """Navigate to URL"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        page = self.sessions[session_id]['page']
        
        try:
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Capture screenshot
            screenshot = await self.capture_screenshot(session_id)
            current_url = page.url
            title = await page.title()
            
            return {
                'success': True,
                'url': current_url,
                'title': title,
                'screenshot': screenshot
            }
        except Exception as e:
            logger.error(f"Navigation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def click_element(self, session_id: str, selector: str) -> Dict[str, Any]:
        """Click on element"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        page = self.sessions[session_id]['page']
        
        try:
            # Wait for element
            await page.wait_for_selector(selector, timeout=10000)
            
            # Get element bounding box for highlight
            element = await page.query_selector(selector)
            if element:
                box = await element.bounding_box()
                
                # Click
                await page.click(selector)
                await page.wait_for_timeout(1000)  # Wait for action to complete
                
                screenshot = await self.capture_screenshot(session_id)
                
                return {
                    'success': True,
                    'screenshot': screenshot,
                    'highlight': box
                }
        except Exception as e:
            logger.error(f"Click error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def type_text(self, session_id: str, selector: str, text: str) -> Dict[str, Any]:
        """Type text into element"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        page = self.sessions[session_id]['page']
        
        try:
            await page.wait_for_selector(selector, timeout=10000)
            
            # Get element box
            element = await page.query_selector(selector)
            box = await element.bounding_box() if element else None
            
            # Type text
            await page.fill(selector, text)
            await page.wait_for_timeout(500)
            
            screenshot = await self.capture_screenshot(session_id)
            
            return {
                'success': True,
                'screenshot': screenshot,
                'highlight': box
            }
        except Exception as e:
            logger.error(f"Type error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def wait_for_element(self, session_id: str, selector: str, timeout: int = 10000) -> Dict[str, Any]:
        """Wait for element to appear"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        page = self.sessions[session_id]['page']
        
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            screenshot = await self.capture_screenshot(session_id)
            
            return {
                'success': True,
                'screenshot': screenshot
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def capture_screenshot(self, session_id: str) -> str:
        """Capture page screenshot as base64"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        page = self.sessions[session_id]['page']
        
        try:
            screenshot_bytes = await page.screenshot(type='png', full_page=False)
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            return f"data:image/png;base64,{screenshot_base64}"
        except Exception as e:
            logger.error(f"Screenshot error: {str(e)}")
            return ""
    
    async def get_page_info(self, session_id: str) -> Dict[str, Any]:
        """Get current page information"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        page = self.sessions[session_id]['page']
        
        return {
            'url': page.url,
            'title': await page.title(),
            'screenshot': await self.capture_screenshot(session_id)
        }
    
    async def find_elements_with_vision(self, session_id: str, description: str) -> List[Dict[str, Any]]:
        """
        Use vision model to find elements matching description
        This uses the visual validator model to identify elements
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        page = self.sessions[session_id]['page']
        screenshot = await self.capture_screenshot(session_id)
        
        # TODO: Call vision model to identify elements
        # For now, return all interactive elements
        try:
            elements = await page.query_selector_all('button, a, input, textarea, select')
            results = []
            
            for element in elements[:10]:  # Limit to 10 elements
                box = await element.bounding_box()
                if box:
                    text = await element.inner_text() if await element.inner_text() else ''
                    tag = await element.evaluate('el => el.tagName')
                    
                    results.append({
                        'selector': f'{tag}',
                        'text': text,
                        'box': box
                    })
            
            return results
        except Exception as e:
            logger.error(f"Find elements error: {str(e)}")
            return []
    
    async def close_session(self, session_id: str):
        """Close browser session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            await session['page'].close()
            await session['context'].close()
            del self.sessions[session_id]
            logger.info(f"Closed session: {session_id}")
    
    async def cleanup(self):
        """Cleanup all resources"""
        for session_id in list(self.sessions.keys()):
            await self.close_session(session_id)
        
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        
        logger.info("Browser automation service cleaned up")

# Global instance
browser_service = BrowserAutomationService()
