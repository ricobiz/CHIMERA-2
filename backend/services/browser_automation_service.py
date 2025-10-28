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
        # Grid config defaults (denser grid by default)
        self.grid_rows = 24
        self.grid_cols = 16
        
    async def initialize(self):
        """Initialize Playwright and browser with anti-detect"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            try:
                self.browser = await self.playwright.chromium.launch(
                    headless=False,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-features=IsolateOrigins,site-per-process'
                    ]
                )
                logger.info("✅ Browser launched headful with anti-detect")
            except Exception as e:
                logger.warning(f"Headful launch failed ({e}); falling back to headless")
                self.browser = await self.playwright.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-features=IsolateOrigins,site-per-process'
                    ]
                )
                logger.info("✅ Browser launched headless with anti-detect fallback")
            
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
        context_options: Dict[str, Any] = {
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
        
        # Create context and page
        context = await self.browser.new_context(**context_options)
        # Apply advanced fingerprinting evasion
        try:
            await AntiDetectFingerprint.apply_fingerprinting_evasion(context)
        except Exception as e:
            logger.warning(f"Fingerprint evasion failed: {e}")
        page = await context.new_page()
        
        self.sessions[session_id] = {
            'context': context,
            'page': page,
            'history': [],
            'use_proxy': use_proxy
        }
        
        logger.info(f"✅ Created session: {session_id} (proxy={use_proxy})")
        return {'session_id': session_id, 'status': 'ready', 'proxy_enabled': use_proxy}
    
    async def create_session_from_profile(self, profile_id: str, session_id: str, fingerprint: Dict[str, Any], proxy: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        await self.initialize()
        user_agent = fingerprint.get('user_agent')
        viewport = fingerprint.get('viewport', {'width': 1366, 'height': 768})
        context_options = {
            'viewport': viewport,
            'user_agent': user_agent,
            'locale': fingerprint.get('locale', 'en-US'),
            'timezone_id': fingerprint.get('timezone_id', 'America/New_York'),
            'record_video_dir': None,
            'storage_state': None,  # will be overridden by profile storage_state if exists
        }
        # Apply proxy if provided
        if proxy:
            context_options['proxy'] = {
                'server': proxy['server'],
                'username': proxy.get('username'),
                'password': proxy.get('password')
            }
        # Persistent dir
        user_data_dir = f"/app/runtime/profiles/{profile_id}"
        os.makedirs(user_data_dir, exist_ok=True)
        # Load storage_state if exists
        storage_path = f"/app/runtime/profiles/{profile_id}/storage_state.json"
        if os.path.exists(storage_path):
            context_options['storage_state'] = storage_path
        # Create context
        context = await self.browser.new_context(**context_options)
        await AntiDetectFingerprint.apply_profile(context, fingerprint)
        page = await context.new_page()
        self.sessions[session_id] = {'context': context, 'page': page, 'history': [], 'use_proxy': bool(proxy), 'profile_id': profile_id}
        logger.info(f"✅ Session from profile created: {session_id} (profile={profile_id})")
        return {'session_id': session_id, 'status': 'ready', 'profile_id': profile_id}

    async def close_session(self, session_id: str) -> bool:
        try:
            if session_id in self.sessions:
                ctx = self.sessions[session_id]['context']
                await ctx.close()
                del self.sessions[session_id]
                logger.info(f"✅ Closed session {session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Close session error: {e}")
            return False
    
    async def navigate(self, session_id: str, url: str) -> Dict[str, Any]:
        """Navigate to URL"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        page = self.sessions[session_id]['page']
        
        try:
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Auto-detect and solve CAPTCHA if present
            if self.captcha_solver:
                await asyncio.sleep(2)  # Wait for CAPTCHA to load
                captcha_solved = await self.captcha_solver.auto_solve(page)
                if captcha_solved:
                    logger.info("✅ CAPTCHA handled automatically")
            
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
    
    async def detect_and_solve_captcha(self, session_id: str) -> Dict[str, Any]:
        """Manually trigger CAPTCHA detection and solving"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        page = self.sessions[session_id]['page']
        
        if not self.captcha_solver:
            return {
                'success': False,
                'error': 'CAPTCHA solver not initialized'
            }
        
        try:
            solved = await self.captcha_solver.auto_solve(page)
            screenshot = await self.capture_screenshot(session_id)
            
            return {
                'success': solved,
                'screenshot': screenshot,
                'message': 'CAPTCHA solved' if solved else 'No CAPTCHA found or solving failed'
            }
        except Exception as e:
            logger.error(f"CAPTCHA solving error: {str(e)}")
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
    
    async def type_text(self, session_id: str, selector: str, text: str, human_like: bool = True) -> Dict[str, Any]:
        """Type text into element with optional human-like behavior"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        page = self.sessions[session_id]['page']
        
        try:
            await page.wait_for_selector(selector, timeout=10000)
            
            # Get element box
            element = await page.query_selector(selector)
            box = await element.bounding_box() if element else None
            
            if human_like:
                # Human-like typing with realistic delays and occasional typos
                await HumanBehaviorSimulator.human_type(page, selector, text)
            else:
                # Fast typing
                await page.fill(selector, text)
            
            await human_like_delay(300, 800)
            
            screenshot = await self.capture_screenshot(session_id)
            
            return {
                'success': True,
                'screenshot': screenshot,
                'highlight': box,
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
        """Capture page screenshot as base64 (no data: prefix)"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        page = self.sessions[session_id]['page']
        
        try:
            screenshot_bytes = await page.screenshot(type='png', full_page=False)
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            return f"{screenshot_base64}"
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
        NO API CALLS - uses fallback DOM heuristics currently
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        page = self.sessions[session_id]['page']
        
        try:
            # Capture screenshot
            screenshot = await self.capture_screenshot(session_id)
            
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
            
            logger.info(f"Found {len(results)} elements for '{description}' (vision disabled, using text search)")
            return results
            
        except Exception as e:
            logger.error(f"Element finding error: {str(e)}")
            return []
    
    async def _inject_grid_overlay(self, page: Page) -> None:
        """Inject a lightweight grid overlay and DOM clickables collector."""
        js = """
        (() => {
          if (window.__chimeraGrid) return;
          const style = document.createElement('style');
          style.textContent = `
            .chimera-grid-cell { position: fixed; border: 1px dashed rgba(150,150,150,0.15); pointer-events: none; z-index: 2147483646; }
            .chimera-grid-label { position: fixed; font: 10px monospace; color: rgba(200,200,200,0.35); background: rgba(0,0,0,0.2); padding: 1px 2px; border-radius: 2px; z-index: 2147483647; pointer-events: none; }
            .chimera-grid-block { position: fixed; z-index: 2147483644; pointer-events: all; background: transparent; }
          `;
          document.head.appendChild(style);
          const overlay = document.createElement('div');
          overlay.id = 'chimera-grid-overlay';
          overlay.style.position = 'fixed';
          overlay.style.top = '0';
          overlay.style.left = '0';
          overlay.style.right = '0';
          overlay.style.bottom = '0';
          overlay.style.pointerEvents = 'none';
          overlay.style.display = 'none';
          overlay.style.zIndex = '2147483645';
          document.body.appendChild(overlay);

          const blockers = document.createElement('div');
          blockers.id = 'chimera-grid-blockers';
          blockers.style.position = 'fixed';
          blockers.style.top = '0';
          blockers.style.left = '0';
          blockers.style.right = '0';
          blockers.style.bottom = '0';
          blockers.style.pointerEvents = 'none';
          blockers.style.display = 'none';
          blockers.style.zIndex = '2147483643';
          document.body.appendChild(blockers);

          function layoutGrid(rows, cols) {
            overlay.innerHTML = '';
            const vw = window.innerWidth, vh = window.innerHeight;
            const cw = vw / cols, ch = vh / rows;
            const A = 'A'.charCodeAt(0);
            for (let r = 0; r < rows; r++) {
              for (let c = 0; c < cols; c++) {
                const cell = document.createElement('div');
                cell.className = 'chimera-grid-cell';
                // hit blocker to allow clicking even if DOM intercepts pointer events
                const hit = document.createElement('div');
                hit.className = 'chimera-grid-block';
                cell.style.left = (c * cw) + 'px';
                cell.style.top = (r * ch) + 'px';
                cell.style.width = cw + 'px';
                cell.style.height = ch + 'px';
                overlay.appendChild(cell);
                // place blocker
                hit.style.left = (c * cw) + 'px';
                hit.style.top = (r * ch) + 'px';
                hit.style.width = cw + 'px';
                hit.style.height = ch + 'px';
                blockers.appendChild(hit);
                const label = document.createElement('div');
                label.className = 'chimera-grid-label';
                label.style.left = (c * cw + 3) + 'px';
                label.style.top = (r * ch + 2) + 'px';
                label.textContent = String.fromCharCode(A + c) + (r + 1);
                overlay.appendChild(label);
              }
            }
          }

          window.__chimeraGrid = {
            show: (rows, cols) => { layoutGrid(rows, cols); overlay.style.display = 'block'; },
            hide: () => { overlay.style.display = 'none'; },
            collect: () => {
              const vw = window.innerWidth, vh = window.innerHeight;
              const clickables = [];
              const candidates = Array.from(document.querySelectorAll('a,button,input,textarea,select,[role="button"], [onclick]'));
              for (const el of candidates) {
                const rect = el.getBoundingClientRect();
                if (!rect || rect.width < 6 || rect.height < 6) continue;
                const style = window.getComputedStyle(el);
                if (style.visibility === 'hidden' || style.display === 'none') continue;
                const label = (el.innerText || el.value || el.getAttribute('aria-label') || el.name || '').slice(0, 64);
                const type = (el.tagName || 'button').toLowerCase();
                clickables.push({
                  bbox: { x: Math.max(0, Math.floor(rect.left)), y: Math.max(0, Math.floor(rect.top)), w: Math.floor(rect.width), h: Math.floor(rect.height) },
                  label,
                  type,
                  confidence: 0.8
                });
              }
              return { vw, vh, clickables };
            },
            flashCell: (cell) => {
              // Visual feedback: briefly highlight a cell
              const vw = window.innerWidth, vh = window.innerHeight;
              const col = cell.charCodeAt(0) - 'A'.charCodeAt(0);
              const row = parseInt(cell.slice(1), 10) - 1;
              const cw = vw / window.__chimeraGrid.__cols;
              const ch = vh / window.__chimeraGrid.__rows;
              const box = document.createElement('div');
              box.style.position = 'fixed';
              box.style.left = (col*cw) + 'px';
              box.style.top = (row*ch) + 'px';
              box.style.width = cw + 'px';
              box.style.height = ch + 'px';
              box.style.border = '2px solid rgba(0,200,255,0.9)';
              box.style.borderRadius = '2px';
              box.style.zIndex = '2147483647';
              box.style.pointerEvents = 'none';
              document.body.appendChild(box);
              setTimeout(()=> box.remove(), 450);
            },
            __rows: 12,
            __cols: 8,
            setGrid: (rows, cols) => { window.__chimeraGrid.__rows = rows; window.__chimeraGrid.__cols = cols; }
          };
        })();
        """
        await page.add_init_script(js)

    async def _collect_dom_clickables(self, page: Page) -> Dict[str, Any]:
        try:
            data = await page.evaluate("window.__chimeraGrid ? window.__chimeraGrid.collect() : null")
            if not data:
                await self._inject_grid_overlay(page)
                data = await page.evaluate("window.__chimeraGrid.collect()")
            return data
        except Exception:
            return {"vw": 1280, "vh": 800, "clickables": []}

    async def _augment_with_vision(self, screenshot_base64: str, dom_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        from .local_vision_service import local_vision_service
        vw, vh = dom_data.get('vw', 1280), dom_data.get('vh', 800)
        dom_clickables = dom_data.get('clickables', [])
        return local_vision_service.detect(screenshot_base64, vw, vh, dom_clickables=dom_clickables, model_path=os.path.join('/app/backend/models/', 'ui-detector.onnx'), rows=self.grid_rows, cols=self.grid_cols)

    # Convenience actions for SCROLL and WAIT
    async def scroll(self, session_id: str, dx: int = 0, dy: int = 400) -> Dict[str, Any]:
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        page = self.sessions[session_id]['page']
        try:
            await page.mouse.wheel(dx, dy)
            await human_like_delay(200, 500)
            screenshot_b64 = await self.capture_screenshot(session_id)
            dom_data = await self._collect_dom_clickables(page)
            vision = await self._augment_with_vision(screenshot_b64, dom_data)
            return {
                "screenshot_base64": screenshot_b64,
                "vision": vision,
                "status": "idle"
            }
        except Exception as e:
            logger.error(f"Scroll error: {e}")
            return {"error": str(e)}

    async def wait(self, ms: int = 500):
        await human_like_delay(ms, ms + 50)

# Global instance
browser_service = BrowserAutomationService()
