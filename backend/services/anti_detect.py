"""
Advanced Anti-Detection Module for Browser Automation
Implements modern anti-detect browser techniques (2025)
"""
import random
import math
import asyncio
import logging
from typing import List, Tuple, Dict, Any, Optional
from playwright.async_api import Page

logger = logging.getLogger(__name__)

class HumanBehaviorSimulator:
    """Simulates human-like behavior patterns"""

    @staticmethod
    def generate_bezier_curve(start: Tuple[float, float], end: Tuple[float, float], control_points: int = 2) -> List[Tuple[float, float]]:
        x1, y1 = start
        x2, y2 = end
        # Random control points
        control_x1 = x1 + (x2 - x1) * random.uniform(0.2, 0.4) + random.uniform(-50, 50)
        control_y1 = y1 + (y2 - y1) * random.uniform(0.2, 0.4) + random.uniform(-50, 50)
        control_x2 = x1 + (x2 - x1) * random.uniform(0.6, 0.8) + random.uniform(-50, 50)
        control_y2 = y1 + (y2 - y1) * random.uniform(0.6, 0.8) + random.uniform(-50, 50)
        # Number of points
        num_points = int(math.sqrt((x2-x1)**2 + (y2-y1)**2) / 2)
        num_points = max(10, min(num_points, 100))
        points = []
        for i in range(num_points):
            t = i / num_points
            x = (1-t)**3 * x1 + 3 * (1-t)**2 * t * control_x1 + 3 * (1-t) * t**2 * control_x2 + t**3 * x2
            y = (1-t)**3 * y1 + 3 * (1-t)**2 * t * control_y1 + 3 * (1-t) * t**2 * control_y2 + t**3 * y2
            # Micro jitter
            x += random.uniform(-1.5, 1.5)
            y += random.uniform(-1.5, 1.5)
            points.append((int(x), int(y)))
        return points

    @staticmethod
    async def human_mouse_move(page: Page, target_x: int, target_y: int, speed_factor: float = 1.0):
        try:
            current_x, current_y = 640, 360
            path = HumanBehaviorSimulator.generate_bezier_curve((current_x, current_y), (target_x, target_y))
            for i, (x, y) in enumerate(path):
                if i < len(path) * 0.3:
                    delay = random.uniform(0.003, 0.008) / speed_factor
                elif i > len(path) * 0.7:
                    delay = random.uniform(0.005, 0.015) / speed_factor
                else:
                    delay = random.uniform(0.002, 0.005) / speed_factor
                await page.mouse.move(x, y)
                await asyncio.sleep(delay)
            # Overshoot (30%)
            if random.random() < 0.3:
                ox = target_x + random.randint(-5, 5)
                oy = target_y + random.randint(-5, 5)
                await page.mouse.move(ox, oy)
                await asyncio.sleep(random.uniform(0.05, 0.15))
                await page.mouse.move(target_x, target_y)
        except Exception as e:
            logger.warning(f"Human mouse move failed: {e}, using direct move")
            await page.mouse.move(target_x, target_y)

    @staticmethod
    async def human_move(page: Page, target_x: int, target_y: int, speed_factor: float = 1.0):
        await HumanBehaviorSimulator.human_mouse_move(page, target_x, target_y, speed_factor)

    @staticmethod
    async def _hover_with_jitter(page: Page, x: int, y: int):
        # Small hover movements around target
        for _ in range(random.randint(2, 4)):
            jx = x + random.randint(-10, 10)
            jy = y + random.randint(-10, 10)
            await page.mouse.move(jx, jy)
            await asyncio.sleep(random.uniform(0.05, 0.15))
        await page.mouse.move(x, y)

    @staticmethod
    async def human_click(page: Page, x: int, y: int, button: str = "left"):
        # Offset from perfect center
        tx = int(x + random.uniform(-6, 6))
        ty = int(y + random.uniform(-6, 6))
        await HumanBehaviorSimulator.human_mouse_move(page, tx, ty)
        await HumanBehaviorSimulator._hover_with_jitter(page, tx, ty)
        await asyncio.sleep(random.uniform(0.2, 0.8))
        # Missclick (5%)
        if random.random() < 0.05:
            mx = tx + random.randint(20, 50)
            my = ty + random.randint(20, 50)
            await page.mouse.down(button=button)
            await asyncio.sleep(random.uniform(0.05, 0.12))
            await page.mouse.up(button=button)
            await asyncio.sleep(random.uniform(0.3, 0.6))
            await HumanBehaviorSimulator.human_mouse_move(page, tx, ty)
            await asyncio.sleep(random.uniform(0.2, 0.6))
        await page.mouse.down(button=button)
        await asyncio.sleep(random.uniform(0.05, 0.15))
        await page.mouse.up(button=button)
        if random.random() < 0.4:
            micro_x = tx + random.randint(-3, 3)
            micro_y = ty + random.randint(-3, 3)
            await page.mouse.move(micro_x, micro_y)

    @staticmethod
    async def human_type(page: Page, selector: Optional[str], text: str):
        element = None
        if selector:
            element = await page.query_selector(selector)
            if not element:
                logger.warning(f"Element {selector} not found; typing to active element")
        if element:
            await element.click()
        await asyncio.sleep(random.uniform(0.1, 0.3))
        for i, char in enumerate(text):
            # Typo (5%)
            if random.random() < 0.05 and i > 0:
                wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                await page.keyboard.type(wrong_char, delay=int(random.uniform(50, 150)))
                await asyncio.sleep(random.uniform(0.1, 0.3))
                await page.keyboard.press('Backspace')
                await asyncio.sleep(random.uniform(0.05, 0.15))
            # Type char
            base_delay = random.gauss(150, 80)
            delay_ms = int(max(60, min(350, base_delay)))
            await page.keyboard.type(char, delay=delay_ms)

    @staticmethod
    async def human_drag(page: Page, sx: int, sy: int, ex: int, ey: int, speed_factor: float = 1.0):
        try:
            await HumanBehaviorSimulator.human_mouse_move(page, sx, sy, speed_factor)
            await asyncio.sleep(random.uniform(0.05, 0.15))
            await page.mouse.down(button="left")
            await asyncio.sleep(random.uniform(0.05, 0.12))
            path = HumanBehaviorSimulator.generate_bezier_curve((sx, sy), (ex, ey))
            for i, (x, y) in enumerate(path):
                if i < len(path) * 0.3:
                    delay = random.uniform(0.003, 0.008) / speed_factor
                elif i > len(path) * 0.7:
                    delay = random.uniform(0.005, 0.015) / speed_factor
                else:
                    delay = random.uniform(0.002, 0.005) / speed_factor
                await page.mouse.move(x, y)
                await asyncio.sleep(delay)
            # End correction
            if random.random() < 0.3:
                await page.mouse.move(ex + random.randint(-5, 5), ey)
                await asyncio.sleep(random.uniform(0.05, 0.15))
            await page.mouse.up(button="left")
        except Exception as e:
            logger.warning(f"Human drag failed: {e}, using direct drag")
            await page.mouse.move(sx, sy)
            await page.mouse.down()
            await page.mouse.move(ex, ey)
            await page.mouse.up()

    @staticmethod
    async def human_scroll(page: Page, total_dy: int):
        scrolled = 0
        direction = 1 if total_dy >= 0 else -1
        total = abs(total_dy)
        while scrolled < total:
            chunk = random.randint(200, 600)
            chunk = min(chunk, total - scrolled)
            await page.mouse.wheel(0, direction * chunk)
            scrolled += chunk
            await asyncio.sleep(random.uniform(0.5, 2.0))
            if random.random() < 0.15:
                back = random.randint(50, 150)
                await page.mouse.wheel(0, -direction * back)
                await asyncio.sleep(random.uniform(0.3, 0.8))

class AntiDetectFingerprint:
    @staticmethod
    def get_anti_detect_script() -> str:
        return """
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        window.chrome = { runtime: {}, loadTimes: function(){}, csi: function(){}, app: {} };
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
          parameters.name === 'notifications' ? Promise.resolve({ state: Notification.permission }) : originalQuery(parameters)
        );
        Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3] });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
          if (parameter === 37445) return 'Intel Inc.';
          if (parameter === 37446) return 'Intel Iris OpenGL Engine';
          return getParameter.apply(this, arguments);
        };
        """

    @staticmethod
    def generate_profile(region: str = None) -> dict:
        viewport = {
            "width": random.randint(1280, 1440),
            "height": random.randint(720, 900)
        }
        screen = {"width": viewport["width"], "height": viewport["height"]}
        profile = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36",
            "locale": "en-US",
            "languages": ["en-US", "en"],
            "timezone_id": "America/New_York",
            "viewport": viewport,
            "screen": screen,
            "platform": "Win32",
            "hardwareConcurrency": 8,
            "deviceMemory": 8,
            "webgl_vendor": "Intel Inc.",
            "webgl_renderer": "Intel Iris OpenGL Engine",
            "canvas_noise_seed": str(random.randint(100000, 999999))
        }
        return profile

    @staticmethod
    async def apply_profile(context, profile: dict) -> bool:
        try:
            await context.set_extra_http_headers({'Accept-Language': ','.join(profile.get('languages', ['en-US','en']))})
            js = f"""
            Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});
            Object.defineProperty(navigator, 'platform', {{ get: () => '{profile.get('platform','Win32')}' }});
            Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {profile.get('hardwareConcurrency', 8)} }});
            Object.defineProperty(navigator, 'deviceMemory', {{ get: () => {profile.get('deviceMemory', 8)} }});
            Object.defineProperty(navigator, 'languages', {{ get: () => {profile.get('languages', ['en-US','en'])} }});
            Object.defineProperty(navigator, 'language', {{ get: () => '{profile.get('languages', ['en-US'])[0]}' }});
            Object.defineProperty(navigator, 'userAgent', {{ get: () => '{profile.get('user_agent','Mozilla/5.0')}' }});
            if (!window.chrome) {{ window.chrome = {{ runtime: {{}}, loadTimes: function(){{}}, csi: function(){{}}, app: {{}} }}; }}
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
              if (parameter === 37445) return '{profile.get('webgl_vendor','Intel Inc.')}';
              if (parameter === 37446) return '{profile.get('webgl_renderer','Intel Iris OpenGL Engine')}';
              return getParameter.apply(this, arguments);
            }};
            """
            await context.add_init_script(js)
            return True
        except Exception as e:
            logger.error(f"Error applying profile: {e}")
            return False

    @staticmethod
    async def apply_fingerprinting_evasion(context):
        try:
            await context.add_init_script(
                """
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) : originalQuery(parameters)
                );
                """
            )
            return True
        except Exception as e:
            logger.error(f"Error applying fingerprinting evasion: {str(e)}")
            return False
