"""
Advanced Anti-Detection Module for Browser Automation
Implements modern anti-detect browser techniques (2025)
"""
import random
import math
import asyncio
import logging
from typing import List, Tuple, Dict, Any
from playwright.async_api import Page, BrowserContext

logger = logging.getLogger(__name__)

class HumanBehaviorSimulator:
    """Simulates human-like behavior patterns"""
    
    @staticmethod
    def generate_bezier_curve(start: Tuple[float, float], end: Tuple[float, float], 
                              control_points: int = 2) -> List[Tuple[float, float]]:
        """
        Generate smooth Bezier curve for mouse movement
        
        Args:
            start: Starting (x, y) coordinates
            end: Ending (x, y) coordinates
            control_points: Number of control points for curve complexity
            
        Returns:
            List of (x, y) coordinates along the Bezier curve
        """
        x1, y1 = start
        x2, y2 = end
        
        # Generate random control points for natural curve
        control_x1 = x1 + (x2 - x1) * random.uniform(0.2, 0.4) + random.uniform(-50, 50)
        control_y1 = y1 + (y2 - y1) * random.uniform(0.2, 0.4) + random.uniform(-50, 50)
        control_x2 = x1 + (x2 - x1) * random.uniform(0.6, 0.8) + random.uniform(-50, 50)
        control_y2 = y1 + (y2 - y1) * random.uniform(0.6, 0.8) + random.uniform(-50, 50)
        
        # Number of points in curve (more = smoother)
        num_points = int(math.sqrt((x2-x1)**2 + (y2-y1)**2) / 2)
        num_points = max(10, min(num_points, 100))  # Between 10-100 points
        
        points = []
        for i in range(num_points):
            t = i / num_points
            
            # Cubic Bezier formula
            x = (1-t)**3 * x1 + \
                3 * (1-t)**2 * t * control_x1 + \
                3 * (1-t) * t**2 * control_x2 + \
                t**3 * x2
            
            y = (1-t)**3 * y1 + \
                3 * (1-t)**2 * t * control_y1 + \
                3 * (1-t) * t**2 * control_y2 + \
                t**3 * y2
            
            points.append((int(x), int(y)))
        
        return points
    
    @staticmethod
    async def human_mouse_move(page: Page, target_x: int, target_y: int, 
                               speed_factor: float = 1.0):
        """
        Move mouse to target with human-like curved path
        
        Args:
            page: Playwright page object
            target_x: Target X coordinate
            target_y: Target Y coordinate
            speed_factor: Speed multiplier (1.0 = normal, >1 = faster)
        """
        try:
            # Get current mouse position (assume center if unknown)
            current_x, current_y = 640, 360  # Default center position
            
            # Generate curved path
            path = HumanBehaviorSimulator.generate_bezier_curve(
                (current_x, current_y),
                (target_x, target_y)
            )
            
            # Move along path with variable speed
            for i, (x, y) in enumerate(path):
                # Variable delay to simulate human acceleration/deceleration
                if i < len(path) * 0.3:  # Accelerating
                    delay = random.uniform(0.003, 0.008) / speed_factor
                elif i > len(path) * 0.7:  # Decelerating
                    delay = random.uniform(0.005, 0.015) / speed_factor
                else:  # Constant speed
                    delay = random.uniform(0.002, 0.005) / speed_factor
                
                await page.mouse.move(x, y)
                await asyncio.sleep(delay)
            
            # Small random overshoot and correction (human-like)
            if random.random() < 0.3:  # 30% chance of overshoot
                overshoot_x = target_x + random.randint(-5, 5)
                overshoot_y = target_y + random.randint(-5, 5)
                await page.mouse.move(overshoot_x, overshoot_y)
                await asyncio.sleep(random.uniform(0.05, 0.15))
                await page.mouse.move(target_x, target_y)
            
        except Exception as e:
            logger.warning(f"Human mouse move failed: {e}, using direct move")
            await page.mouse.move(target_x, target_y)
    
    @staticmethod
    async def human_click(page: Page, x: int, y: int, button: str = "left"):
        """
        Click with human-like behavior (movement + click + small delay)
        
        Args:
            page: Playwright page object
            x: X coordinate
            y: Y coordinate
            button: Mouse button ("left", "right", "middle")
        """
        # Move to position with human-like curve
        await HumanBehaviorSimulator.human_mouse_move(page, x, y)
        
        # Small pause before click (human hesitation)
        await asyncio.sleep(random.uniform(0.05, 0.15))
        
        # Click with realistic down/up timing
        await page.mouse.down(button=button)
        await asyncio.sleep(random.uniform(0.05, 0.12))  # Human click duration
        await page.mouse.up(button=button)
        
        # Micro movement after click (very human-like)
        if random.random() < 0.4:
            micro_x = x + random.randint(-3, 3)
            micro_y = y + random.randint(-3, 3)
            await page.mouse.move(micro_x, micro_y)
    
    @staticmethod
    async def human_type(page: Page, selector: str, text: str):
        """
        Type text with human-like delays and occasional mistakes
        
        Args:
            page: Playwright page object
            selector: CSS selector of input element
            text: Text to type
        """
        element = await page.query_selector(selector)
        if not element:
            logger.warning(f"Element {selector} not found")
            return
        
        await element.click()
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
        for i, char in enumerate(text):
            # Variable typing speed (fast typists have patterns)
            if char == ' ':
                delay = random.uniform(0.15, 0.35)  # Longer pause for space
            elif char in '.,!?':
                delay = random.uniform(0.2, 0.4)  # Pause after punctuation
            else:
                delay = random.uniform(0.05, 0.15)
            
            # Occasional typo + correction (2% chance)
            if random.random() < 0.02 and i > 0:
                wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                await element.type(wrong_char, delay=delay * 1000)
                await asyncio.sleep(random.uniform(0.1, 0.3))
                await page.keyboard.press('Backspace')
                await asyncio.sleep(random.uniform(0.05, 0.15))
            
            await element.type(char, delay=delay * 1000)
    
    @staticmethod
    async def random_scroll(page: Page):
        """Random human-like scrolling"""
        scroll_amount = random.randint(100, 500) * random.choice([1, -1])
        await page.mouse.wheel(0, scroll_amount)
        await asyncio.sleep(random.uniform(0.3, 1.0))


class AntiDetectFingerprint:
    """Advanced fingerprinting evasion techniques"""
    
    @staticmethod
    def get_anti_detect_script() -> str:
        """
        Returns comprehensive JavaScript to evade detection
        Covers: WebDriver, Canvas, WebGL, Audio, Fonts, Plugins, etc.
        """
        return """
        // ==== WEBDRIVER DETECTION EVASION ====
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // ==== CHROME RUNTIME ====
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
        
        // ==== PERMISSIONS API ====
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // ==== PLUGINS SPOOFING ====
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {
                    0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: Plugin},
                    description: "Portable Document Format",
                    filename: "internal-pdf-viewer",
                    length: 1,
                    name: "Chrome PDF Plugin"
                },
                {
                    0: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: Plugin},
                    description: "Portable Document Format",
                    filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                    length: 1,
                    name: "Chrome PDF Viewer"
                },
                {
                    0: {type: "application/x-nacl", suffixes: "", description: "Native Client Executable", enabledPlugin: Plugin},
                    1: {type: "application/x-pnacl", suffixes: "", description: "Portable Native Client Executable", enabledPlugin: Plugin},
                    description: "Native Client",
                    filename: "internal-nacl-plugin",
                    length: 2,
                    name: "Native Client"
                }
            ]
        });
        
        // ==== LANGUAGES ====
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
        
        // ==== CANVAS FINGERPRINTING EVASION ====
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        const originalToBlob = HTMLCanvasElement.prototype.toBlob;
        const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
        
        // Add subtle noise to canvas data
        const noisify = function(canvas, context) {
            const shift = {
                'r': Math.floor(Math.random() * 10) - 5,
                'g': Math.floor(Math.random() * 10) - 5,
                'b': Math.floor(Math.random() * 10) - 5,
                'a': Math.floor(Math.random() * 10) - 5
            };
            
            const width = canvas.width;
            const height = canvas.height;
            if (width && height) {
                const imageData = originalGetImageData.apply(context, [0, 0, width, height]);
                for (let i = 0; i < imageData.data.length; i += 4) {
                    imageData.data[i] = imageData.data[i] + shift.r;
                    imageData.data[i + 1] = imageData.data[i + 1] + shift.g;
                    imageData.data[i + 2] = imageData.data[i + 2] + shift.b;
                    imageData.data[i + 3] = imageData.data[i + 3] + shift.a;
                }
                context.putImageData(imageData, 0, 0);
            }
        };
        
        HTMLCanvasElement.prototype.toDataURL = function() {
            noisify(this, this.getContext('2d'));
            return originalToDataURL.apply(this, arguments);
        };
        
        // ==== WEBGL FINGERPRINTING EVASION ====
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            // Spoof specific WebGL parameters
            if (parameter === 37445) { // UNMASKED_VENDOR_WEBGL
                return 'Intel Inc.';
            }
            if (parameter === 37446) { // UNMASKED_RENDERER_WEBGL
                return 'Intel Iris OpenGL Engine';
            }
            return getParameter.apply(this, arguments);
        };
        
        // ==== AUDIO CONTEXT FINGERPRINTING ====
        const audioContext = window.AudioContext || window.webkitAudioContext;
        if (audioContext) {
            const OriginalAudioContext = audioContext;
            window.AudioContext = function() {
                const context = new OriginalAudioContext();
                const originalCreateOscillator = context.createOscillator;
                context.createOscillator = function() {
                    const oscillator = originalCreateOscillator.apply(context, arguments);
                    const originalStart = oscillator.start;
                    oscillator.start = function() {
                        // Add slight frequency variation
                        oscillator.frequency.value = oscillator.frequency.value + Math.random() * 0.0001;
                        return originalStart.apply(oscillator, arguments);
                    };
                    return oscillator;
                };
                return context;
            };
        }
        
        // ==== SCREEN RESOLUTION CONSISTENCY ====
        // Ensure screen dimensions match viewport
        Object.defineProperty(screen, 'availWidth', {
            get: () => window.innerWidth
        });
        Object.defineProperty(screen, 'availHeight', {
            get: () => window.innerHeight
        });
        
        // ==== TIMEZONE CONSISTENCY ====
        const originalDateToString = Date.prototype.toString;
        Date.prototype.toString = function() {
            return originalDateToString.call(this).replace(/\\(.*\\)/, '(Eastern Standard Time)');
        };
        
        // ==== BATTERY API (privacy concern) ====
        if (navigator.getBattery) {
            navigator.getBattery = () => Promise.resolve({
                charging: true,
                chargingTime: 0,
                dischargingTime: Infinity,
                level: 1
            });
        }
        
        // ==== CONNECTION API ====
        if (navigator.connection) {
            Object.defineProperty(navigator.connection, 'rtt', {
                get: () => 50
            });
        }
        
        // ==== MEDIA DEVICES ====
        if (navigator.mediaDevices) {
            const originalEnumerateDevices = navigator.mediaDevices.enumerateDevices;
            navigator.mediaDevices.enumerateDevices = function() {
                return originalEnumerateDevices.apply(this, arguments).then(devices => {
                    return devices.map(device => {
                        if (device.kind === 'audioinput') {
                            return {
                                ...device,
                                label: device.label || 'Built-in Microphone',
                                deviceId: device.deviceId || 'default'
                            };
                        }
                        if (device.kind === 'videoinput') {
                            return {
                                ...device,
                                label: device.label || 'Built-in Camera',
                                deviceId: device.deviceId || 'default'
                            };
                        }
                        return device;
                    });
                });
            };
        }
        
        // ==== NOTIFICATION PERMISSION ====
        const originalNotificationPermission = Notification.permission;
        Object.defineProperty(Notification, 'permission', {
            get: () => originalNotificationPermission || 'default'
        });
        
        console.log('🛡️ Advanced anti-detect fingerprinting enabled');
        """
    
    @staticmethod
    async def apply_fingerprinting_evasion(context: BrowserContext):
        """Apply anti-detect script to browser context"""
        try:
            await context.add_init_script(AntiDetectFingerprint.get_anti_detect_script())
            logger.info("✅ Advanced anti-detect fingerprinting applied")
        except Exception as e:
            logger.error(f"Failed to apply fingerprinting evasion: {e}")


class CaptchaSolver:
    """AI-powered CAPTCHA solving using vision models"""
    
    def __init__(self, openrouter_service):
        self.openrouter_service = openrouter_service
        self.vision_model = "google/gemini-2.5-flash-image"  # Fast vision model
    
    async def detect_captcha(self, page: Page) -> Dict[str, Any]:
        """
        Detect if CAPTCHA is present on page
        
        Returns:
            dict with 'present', 'type', 'selector' keys
        """
        try:
            # Check for common CAPTCHA elements
            captcha_selectors = [
                'iframe[src*="recaptcha"]',
                'iframe[src*="hcaptcha"]',
                'iframe[src*="captcha"]',
                '.g-recaptcha',
                '.h-captcha',
                '[class*="captcha"]',
                '#captcha'
            ]
            
            for selector in captcha_selectors:
                element = await page.query_selector(selector)
                if element:
                    captcha_type = 'recaptcha' if 'recaptcha' in selector else \
                                  'hcaptcha' if 'hcaptcha' in selector else 'unknown'
                    return {
                        'present': True,
                        'type': captcha_type,
                        'selector': selector
                    }
            
            return {'present': False}
            
        except Exception as e:
            logger.error(f"CAPTCHA detection failed: {e}")
            return {'present': False}
    
    async def solve_image_captcha(self, page: Page, captcha_element) -> Dict[str, Any]:
        """
        Solve image-based CAPTCHA using vision AI
        
        Args:
            page: Playwright page
            captcha_element: CAPTCHA element or selector
            
        Returns:
            dict with 'solved', 'answer', 'confidence' keys
        """
        try:
            # Take screenshot of CAPTCHA
            screenshot = await page.screenshot(full_page=False)
            screenshot_base64 = screenshot.decode('utf-8') if isinstance(screenshot, bytes) else screenshot
            
            # Use vision model to analyze CAPTCHA
            prompt = """You are a CAPTCHA solver. Analyze this CAPTCHA image and provide the solution.

Instructions:
1. Identify the type of CAPTCHA (text, math, image selection, puzzle, etc.)
2. Solve it accurately
3. Respond ONLY with the solution in this JSON format:

{
  "type": "text|math|selection|puzzle",
  "solution": "your solution here",
  "confidence": 0-100
}

Be precise and accurate."""

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screenshot_base64}"
                            }
                        }
                    ]
                }
            ]
            
            response = await self.openrouter_service.chat_completion(
                messages=messages,
                model=self.vision_model,
                temperature=0.1
            )
            
            result_text = response['choices'][0]['message']['content']
            
            # Parse JSON response
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'\{[^{}]*\}', result_text)
            if json_match:
                result = json.loads(json_match.group(0))
                
                return {
                    'solved': True,
                    'type': result.get('type', 'unknown'),
                    'answer': result.get('solution', ''),
                    'confidence': result.get('confidence', 50)
                }
            
            logger.warning(f"Failed to parse CAPTCHA solution: {result_text}")
            return {'solved': False, 'reason': 'Failed to parse AI response'}
            
        except Exception as e:
            logger.error(f"CAPTCHA solving failed: {e}")
            return {'solved': False, 'reason': str(e)}
    
    async def auto_solve(self, page: Page) -> bool:
        """
        Automatically detect and solve CAPTCHA if present
        
        Returns:
            True if CAPTCHA was solved or not present, False if failed
        """
        try:
            # Detect CAPTCHA
            captcha_info = await self.detect_captcha(page)
            
            if not captcha_info['present']:
                logger.info("No CAPTCHA detected")
                return True
            
            logger.info(f"CAPTCHA detected: {captcha_info['type']}")
            
            # Solve CAPTCHA
            solution = await self.solve_image_captcha(page, captcha_info['selector'])
            
            if solution['solved']:
                logger.info(f"✅ CAPTCHA solved with {solution['confidence']}% confidence")
                
                # Input solution (implementation depends on CAPTCHA type)
                # This is a simplified version
                if solution['type'] == 'text':
                    input_selector = 'input[type="text"]'
                    await HumanBehaviorSimulator.human_type(page, input_selector, solution['answer'])
                    
                    # Submit
                    submit_btn = await page.query_selector('button[type="submit"], input[type="submit"]')
                    if submit_btn:
                        box = await submit_btn.bounding_box()
                        if box:
                            await HumanBehaviorSimulator.human_click(
                                page,
                                int(box['x'] + box['width']/2),
                                int(box['y'] + box['height']/2)
                            )
                
                return True
            else:
                logger.warning(f"CAPTCHA solving failed: {solution.get('reason')}")
                return False
                
        except Exception as e:
            logger.error(f"Auto-solve failed: {e}")
            return False
