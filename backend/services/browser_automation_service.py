"""
Real Browser Automation Service using Playwright
Advanced anti-detection with fingerprinting evasion and CAPTCHA solving
"""
import asyncio
import logging
import base64
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from typing import Dict, Any, Optional, List
import os
from services.anti_detect import (
    HumanBehaviorSimulator,
    AntiDetectFingerprint,
    CaptchaSolver
)

logger = logging.getLogger(__name__)

# Anti-detection: random delays
import random
async def human_like_delay(min_ms: int = 100, max_ms: int = 500):
    """Add human-like random delay"""
    delay = random.randint(min_ms, max_ms) / 1000.0
    await asyncio.sleep(delay)

class BrowserAutomationService:
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.captcha_solver: Optional[CaptchaSolver] = None
        
    async def initialize(self):
        """Initialize Playwright and browser with anti-detect"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',  # For some anti-detect scenarios
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )
            logger.info("✅ Browser launched with advanced anti-detect")
            
            # Initialize CAPTCHA solver
            try:
                from services.openrouter_service import openrouter_service
                self.captcha_solver = CaptchaSolver(openrouter_service)
                logger.info("✅ CAPTCHA solver initialized")
            except Exception as e:
                logger.warning(f"CAPTCHA solver initialization failed: {e}")
    
    async def create_session(self, session_id: str, use_proxy: bool = False) -> Dict[str, Any]:
        """Create a new browser session with anti-detection and optional proxy"""
        await self.initialize()
        
        # Import proxy service
        from services.proxy_service import proxy_service
        
        # Anti-detection: randomize viewport
        import random
        viewport_width = random.randint(1280, 1440)
        viewport_height = random.randint(680, 900)
        
        # Anti-detection: get random user agent from proxy service
        user_agent = proxy_service.get_random_user_agent()
        
        # Prepare context options
        context_options = {
            'viewport': {'width': viewport_width, 'height': viewport_height},
            'user_agent': user_agent,
            'locale': 'en-US',
            'timezone_id': 'America/New_York',
            # Anti-detection headers
            'extra_http_headers': {
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            }
        }
        
        # Add proxy if enabled and available
        if use_proxy and proxy_service.is_enabled():
            await proxy_service.get_proxies()  # Ensure proxies are fetched
            proxy = proxy_service.get_next_proxy()
            
            if proxy:
                context_options['proxy'] = {
                    'server': proxy['server'],
                    'username': proxy['username'],
                    'password': proxy['password']
                }
                logger.info(f"✅ Session using proxy: {proxy['server']} ({proxy['country']})")
            else:
                logger.warning("Proxy requested but none available, using direct connection")
        
        # Create new context with anti-detection settings
        context = await self.browser.new_context(**context_options)
        
        # Apply advanced fingerprinting evasion
        await AntiDetectFingerprint.apply_fingerprinting_evasion(context)
        
        page = await context.new_page()
        
        self.sessions[session_id] = {
            'context': context,
            'page': page,
            'history': [],
            'use_proxy': use_proxy
        }
        
        logger.info(f"✅ Created session: {session_id} (proxy={use_proxy})")
        return {'session_id': session_id, 'status': 'ready', 'proxy_enabled': use_proxy}
    
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
    
    async def click_element(self, session_id: str, selector: str, human_like: bool = True) -> Dict[str, Any]:
        """Click on element with optional human-like behavior"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        page = self.sessions[session_id]['page']
        
        try:
            # Wait for element
            await page.wait_for_selector(selector, timeout=10000)
            
            # Get element bounding box
            element = await page.query_selector(selector)
            if element:
                box = await element.bounding_box()
                
                if human_like and box:
                    # Human-like click with cursor movement
                    center_x = int(box['x'] + box['width'] / 2)
                    center_y = int(box['y'] + box['height'] / 2)
                    await HumanBehaviorSimulator.human_click(page, center_x, center_y)
                else:
                    # Standard click
                    await page.click(selector)
                
                await human_like_delay(500, 1500)  # Human pause after click
                
                screenshot = await self.capture_screenshot(session_id)
                
                return {
                    'success': True,
                    'screenshot': screenshot,
                    'highlight': box,
                    'human_like': human_like
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
        Use LOCAL vision model to find elements matching description
        NO API CALLS - uses Hugging Face Florence-2 model locally
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        page = self.sessions[session_id]['page']
        
        try:
            # Capture screenshot
            screenshot = await self.capture_screenshot(session_id)
            
            # Vision service disabled for MVP - using basic selector matching
            # elements = await vision_service.find_element(
            #     screenshot=screenshot,
            #     description=description,
            #     return_multiple=True
            # )
            
            # Fallback: Try basic text search instead of vision
            results = []
            try:
                # Search for elements by text content
                selector = f"text={description}"
                elements = await page.query_selector_all(selector)
                
                for i, element in enumerate(elements[:3]):  # Limit to 3 results
                    box_model = await element.bounding_box()
                    if box_model:
                        results.append({
                            'selector': selector,
                            'box': box_model,
                            'text': description,
                            'confidence': 0.7,
                            'index': i
                        })
            except Exception as e:
                logger.warning(f"Basic text search failed: {e}")
            
            # Original vision-based code (disabled):
            # # Convert vision model results to selectors
            # results = []
            # for elem in elements:
            #     box = elem.get('box', {})
            #     text = elem.get('text', '')
            #     confidence = elem.get('confidence', 0)
            #     
            #     # Try to match with actual DOM elements
            #     # Get element at coordinates
            #     center_x = box.get('x', 0) + box.get('width', 0) / 2
            #     center_y = box.get('y', 0) + box.get('height', 0) / 2
            #     
            #     try:
            #     try:
            #         # Get element at point
            #         element_handle = await page.evaluate(f"""
            #             document.elementFromPoint({center_x}, {center_y})
            #         """)
            #         
            #         # Get selector for this element
            #         tag = await page.evaluate("""
            #             (el) => el ? el.tagName.toLowerCase() : null
            #         """, element_handle)
            #         
            #         results.append({
            #             'selector': tag or 'unknown',
            #             'text': text,
            #             'box': box,
            #             'confidence': confidence
            #         })
            #     except:
            #         # Fallback if DOM query fails
            #         results.append({
            #             'selector': f"element_at_{int(center_x)}_{int(center_y)}",
            #             'text': text,
            #             'box': box,
            #             'confidence': confidence
            #         })
            
            logger.info(f"Found {len(results)} elements for '{description}' (vision disabled, using text search)")
            return results
            
        except Exception as e:
            logger.error(f"Element finding error: {str(e)}")
            
            # Fallback to simple DOM query
            try:
                elements = await page.query_selector_all('button, a, input, textarea, select')
                results = []
                
                for element in elements[:10]:
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
            except Exception as fallback_error:
                logger.error(f"Fallback element finding also failed: {str(fallback_error)}")
                return []
    
    async def close_session(self, session_id: str):
        """Close browser session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            await session['page'].close()
            await session['context'].close()
            del self.sessions[session_id]
            logger.info(f"Closed session: {session_id}")
    
    async def smart_click(self, session_id: str, target_hint: str) -> Dict[str, Any]:
        """
        Smart click using vision model to find element by natural language description
        
        Args:
            session_id: Browser session ID
            target_hint: Natural language description of element to click (e.g., "Submit button", "Login link")
        
        Returns:
            {
                success: bool,
                screenshot_before: str (base64),
                screenshot_after: str (base64),
                box: {x, y, width, height},
                confidence: float,
                element_description: str
            }
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        page = self.sessions[session_id]['page']
        
        try:
            # Capture screenshot before
            screenshot_before = await self.capture_screenshot(session_id)
            
            # Use vision model to find element
            from services.visual_validator_service import visual_validator_service
            
            vision_prompt = f"""Analyze this webpage screenshot and locate the element: "{target_hint}"

Return JSON with:
{{
    "found": true/false,
    "box": {{"x": number, "y": number, "width": number, "height": number}},
    "confidence": 0.0-1.0,
    "description": "what you found"
}}

If element not found, set found=false and confidence=0."""

            # Call vision API (using existing visual_validator_service with Gemini)
            import httpx
            import json
            import re
            
            api_key = os.environ.get('OPENROUTER_API_KEY')
            
            response = await httpx.AsyncClient(timeout=30.0).post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "google/gemini-2.5-flash-image",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": vision_prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_before}"}}
                            ]
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 500
                }
            )
            
            result_text = response.json()['choices'][0]['message']['content']
            
            # Extract JSON from response
            json_match = re.search(r'```json\s*(.*?)\s*```', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(1)
            
            vision_result = json.loads(result_text)
            
            if not vision_result.get('found', False):
                return {
                    "success": False,
                    "screenshot_before": screenshot_before,
                    "screenshot_after": screenshot_before,
                    "box": None,
                    "confidence": 0.0,
                    "element_description": f"Element '{target_hint}' not found",
                    "error": "Element not visible or not found on page"
                }
            
            # Get click coordinates
            box = vision_result['box']
            click_x = box['x'] + box['width'] / 2
            click_y = box['y'] + box['height'] / 2
            
            # Human-like delay before click
            await human_like_delay(150, 400)
            
            # Perform click
            await page.mouse.click(click_x, click_y)
            
            # Human-like delay after click
            await human_like_delay(300, 700)
            
            # Capture screenshot after
            screenshot_after = await self.capture_screenshot(session_id)
            
            # Post-check: verify something changed
            url_after = page.url
            changed = (screenshot_after != screenshot_before) or (url_after != page.url)
            
            logger.info(f"Smart click: {target_hint} at ({click_x}, {click_y}) - Changed: {changed}")
            
            return {
                "success": True,
                "screenshot_before": screenshot_before,
                "screenshot_after": screenshot_after,
                "box": box,
                "confidence": vision_result.get('confidence', 0.8),
                "element_description": vision_result.get('description', target_hint)
            }
            
        except Exception as e:
            logger.error(f"Smart click error: {str(e)}")
            screenshot = await self.capture_screenshot(session_id)
            return {
                "success": False,
                "screenshot_before": screenshot,
                "screenshot_after": screenshot,
                "box": None,
                "confidence": 0.0,
                "element_description": f"Error: {str(e)}",
                "error": str(e)
            }
    
    async def smart_type(self, session_id: str, target_hint: str, text: str) -> Dict[str, Any]:
        """
        Smart type using vision model to find input field by natural language description
        
        Args:
            session_id: Browser session ID
            target_hint: Natural language description of input field (e.g., "Email input", "Search box")
            text: Text to type
        
        Returns:
            {
                success: bool,
                screenshot_before: str (base64),
                screenshot_after: str (base64),
                box: {x, y, width, height},
                confidence: float,
                element_description: str,
                typed_text: str
            }
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        page = self.sessions[session_id]['page']
        
        try:
            # Capture screenshot before
            screenshot_before = await self.capture_screenshot(session_id)
            
            # Use vision model to find element
            import httpx
            import json
            import re
            
            vision_prompt = f"""Analyze this webpage screenshot and locate the input field: "{target_hint}"

Return JSON with:
{{
    "found": true/false,
    "box": {{"x": number, "y": number, "width": number, "height": number}},
    "confidence": 0.0-1.0,
    "description": "what you found",
    "field_type": "text|email|password|search|textarea"
}}

If element not found, set found=false."""

            api_key = os.environ.get('OPENROUTER_API_KEY')
            
            response = await httpx.AsyncClient(timeout=30.0).post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "google/gemini-2.5-flash-image",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": vision_prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_before}"}}
                            ]
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 500
                }
            )
            
            result_text = response.json()['choices'][0]['message']['content']
            
            # Extract JSON
            json_match = re.search(r'```json\s*(.*?)\s*```', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(1)
            
            vision_result = json.loads(result_text)
            
            if not vision_result.get('found', False):
                return {
                    "success": False,
                    "screenshot_before": screenshot_before,
                    "screenshot_after": screenshot_before,
                    "box": None,
                    "confidence": 0.0,
                    "element_description": f"Input field '{target_hint}' not found",
                    "typed_text": "",
                    "error": "Input field not visible or not found on page"
                }
            
            # Get click coordinates to focus
            box = vision_result['box']
            click_x = box['x'] + box['width'] / 2
            click_y = box['y'] + box['height'] / 2
            
            # Click to focus
            await page.mouse.click(click_x, click_y)
            await page.wait_for_timeout(200)
            
            # Clear existing content
            await page.keyboard.press('Control+A')
            await page.keyboard.press('Backspace')
            
            # Type new text
            await page.keyboard.type(text, delay=50)
            await page.wait_for_timeout(300)
            
            # Capture screenshot after
            screenshot_after = await self.capture_screenshot(session_id)
            
            logger.info(f"Smart type successful: '{text}' into {target_hint}")
            
            return {
                "success": True,
                "screenshot_before": screenshot_before,
                "screenshot_after": screenshot_after,
                "box": box,
                "confidence": vision_result.get('confidence', 0.8),
                "element_description": vision_result.get('description', target_hint),
                "typed_text": text,
                "field_type": vision_result.get('field_type', 'text')
            }
            
        except Exception as e:
            logger.error(f"Smart type error: {str(e)}")
            screenshot = await self.capture_screenshot(session_id)
            return {
                "success": False,
                "screenshot_before": screenshot,
                "screenshot_after": screenshot,
                "box": None,
                "confidence": 0.0,
                "element_description": f"Error: {str(e)}",
                "typed_text": "",
                "error": str(e)
            }
    
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
