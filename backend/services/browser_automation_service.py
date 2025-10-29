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
    
    async def create_session_from_profile(self, profile_id: str, session_id: str, fingerprint: Optional[Dict[str, Any]] = None, proxy: Optional[Dict[str, Any]] = None, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create session strictly from profile meta (preferred), fallback to fingerprint dict."""
        await self.initialize()
        context_options: Dict[str, Any] = {}
        if meta:
            # New meta structure support
            browser = meta.get('browser', {})
            locale = meta.get('locale', {})
            proxy_meta = meta.get('proxy', {})
            context_options = {
                'viewport': browser.get('viewport') or {'width': 1366, 'height': 768},
                'user_agent': browser.get('user_agent'),
                'locale': locale.get('locale', 'en-US'),
                'timezone_id': locale.get('timezone_id', 'America/New_York'),
                'accept_downloads': True,
            }
            # storage_state
            storage_path = f"/app/runtime/profiles/{profile_id}/storage_state.json"
            if os.path.exists(storage_path):
                context_options['storage_state'] = storage_path
            # proxy settings
            if proxy_meta and proxy_meta.get('url'):
                context_options['proxy'] = {'server': proxy_meta.get('url')}
        else:
            # Backward compatibility
            fp = fingerprint or {}
            context_options = {
                'viewport': fp.get('viewport', {'width': 1366, 'height': 768}),
                'user_agent': fp.get('user_agent'),
                'locale': fp.get('locale', 'en-US'),
                'timezone_id': fp.get('timezone_id', 'America/New_York'),
                'record_video_dir': None,
            }
            if proxy:
                context_options['proxy'] = {
                    'server': proxy['server'],
                    'username': proxy.get('username'),
                    'password': proxy.get('password')
                }
            storage_path = f"/app/runtime/profiles/{profile_id}/storage_state.json"
            if os.path.exists(storage_path):
                context_options['storage_state'] = storage_path
        # Create context
        context = await self.browser.new_context(**context_options)
        # Apply anti-detect patches based on provided data
        try:
            await AntiDetectFingerprint.apply_profile(context, meta or fingerprint or {})
        except Exception as e:
            logger.warning(f"apply_profile failed: {e}")
        page = await context.new_page()
        self.sessions[session_id] = {'context': context, 'page': page, 'history': [], 'use_proxy': bool(proxy or (meta and meta.get('proxy'))), 'profile_id': profile_id}
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
            
            # ВАЖНО: Ждём полной загрузки страницы
            await self.wait_for_page_ready(page)
            
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
    
    async def wait_for_page_ready(self, page: Page, timeout_ms: int = 10000) -> bool:
        """
        Ждёт полной загрузки страницы (не только DOM, но и скрипты, стили).
        Проверяет:
        1. document.readyState = 'complete'
        2. Нет активных network запросов (networkidle)
        3. Стабильность DOM (количество элементов не меняется)
        4. Нет loading спиннеров
        """
        try:
            # 1. Ждём document.readyState = 'complete'
            await page.wait_for_load_state('load', timeout=timeout_ms)
            
            # 2. Ждём network idle
            await page.wait_for_load_state('networkidle', timeout=timeout_ms)
            
            # 3. Проверяем стабильность DOM (2 проверки с интервалом 500ms)
            count1 = await page.evaluate("() => document.querySelectorAll('*').length")
            await asyncio.sleep(0.5)
            count2 = await page.evaluate("() => document.querySelectorAll('*').length")
            
            if abs(count2 - count1) > 5:
                # DOM ещё меняется, ждём ещё немного
                logger.debug(f"DOM still changing: {count1} → {count2}, waiting...")
                await asyncio.sleep(1)
            
            # 4. Проверяем нет ли loading индикаторов
            loading_selectors = [
                '[class*="loading"]',
                '[class*="spinner"]',
                '[class*="loader"]',
                '[aria-busy="true"]'
            ]
            
            for selector in loading_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    visible_loaders = []
                    for el in elements:
                        is_visible = await el.is_visible()
                        if is_visible:
                            visible_loaders.append(el)
                    
                    if visible_loaders:
                        logger.debug(f"Found {len(visible_loaders)} visible loading indicators, waiting...")
                        await asyncio.sleep(1)
                except Exception:
                    pass
            
            logger.debug("✅ Page fully loaded and stable")
            return True
            
        except Exception as e:
            logger.warning(f"wait_for_page_ready timeout or error: {e}")
            return False
    
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
            show: (rows, cols) => { layoutGrid(rows, cols); overlay.style.display = 'block'; blockers.style.display = 'block'; },
            hide: () => { overlay.style.display = 'none'; blockers.style.display = 'none'; },
            collect: () => {
              const vw = window.innerWidth, vh = window.innerHeight;
              const clickables = [];
              function push(el, offX, offY, label, type, score=0.8) {
                const rect = el.getBoundingClientRect();
                if (!rect || rect.width < 4 || rect.height < 4) return;
                const x = Math.max(0, Math.floor(rect.left + offX));
                const y = Math.max(0, Math.floor(rect.top + offY));
                const w = Math.floor(rect.width);
                const h = Math.floor(rect.height);
                clickables.push({ bbox: { x, y, w, h }, label: (label||'').slice(0,64), type: type||'node', confidence: score });
              }
              function collectIn(doc, offX, offY) {
                const nodes = Array.from(doc.querySelectorAll('a,button,input,textarea,select,[role="button"], [onclick], [role="link"], input[type="submit"], input[type="search"]'));
                for (const el of nodes) {
                  const style = doc.defaultView.getComputedStyle(el);
                  if (!style) continue;
                  if (style.visibility === 'hidden' || style.display === 'none' || style.pointerEvents === 'none') continue;
                  const label = (el.innerText || el.value || el.getAttribute('aria-label') || el.getAttribute('title') || el.name || '').trim();
                  const type = (el.tagName || 'node').toLowerCase();
                  push(el, offX, offY, label, type, 0.8);
                }
                // Aggressive: specific known targets
                const specialQueries = [
                  '[aria-label*="Sign in" i]','a[href*="ServiceLogin"]','a[href*="accounts.google"]','button:has-text("Sign in")','a:has-text("Sign in")',
                  'input[name="q"]','form[role="search"] input','[aria-label*="Search" i] input','input[type="search"]'
                ];
                for (const q of specialQueries) {
                  try {
                    const els = doc.querySelectorAll(q);
                    els.forEach(el => push(el, offX, offY, (el.getAttribute('aria-label')||el.getAttribute('title')||el.innerText||el.getAttribute('name')||q), 'special', 0.9));
                  } catch (e) { /* unsupported selector */ }
                }
              }
              // Top document
              collectIn(document, 0, 0);
              // Try a few same-origin iframes
              const iframes = Array.from(document.querySelectorAll('iframe')).slice(0, 5);
              for (const iframe of iframes) {
                try {
                  const r = iframe.getBoundingClientRect();
                  const idoc = iframe.contentDocument;
                  if (idoc) collectIn(idoc, r.left, r.top);
                } catch (e) { /* cross-origin */ }
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
        # Also run immediately on current document so collect() works without navigation
        try:
            await page.evaluate(js)
        except Exception:
            pass

    async def _collect_dom_clickables(self, page: Page) -> Dict[str, Any]:
        try:
            data = await page.evaluate("window.__chimeraGrid ? window.__chimeraGrid.collect() : null")
            if not data:
                await self._inject_grid_overlay(page)
                data = await page.evaluate("window.__chimeraGrid ? window.__chimeraGrid.collect() : null")
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
            await HumanBehaviorSimulator.human_scroll(page, dy)
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
