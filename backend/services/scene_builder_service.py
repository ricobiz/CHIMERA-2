"""
Scene Builder Service - Converts DOM/AX/Vision → Scene JSON
Implements SB (Scene Builder) from Technical Assignment
"""
import logging
import time
from typing import Dict, Any, List, Optional
from playwright.async_api import Page

logger = logging.getLogger(__name__)

class SceneBuilderService:
    """
    Scene Builder: DOM/AX → elements + OCR + Vision → Scene JSON
    Priority: DOM/AX > OCR > Vision
    """
    
    async def build_scene(
        self, 
        page: Page, 
        dom_data: Dict[str, Any],
        vision_elements: List[Dict[str, Any]],
        session_id: str
    ) -> Dict[str, Any]:
        """
        Build Scene JSON from DOM + Vision data
        
        Returns Scene JSON with:
        - viewport
        - url
        - http status
        - antibot block
        - elements array (id/role/label/bbox/state)
        - hints
        - timestamp
        """
        try:
            # Get page info
            url = page.url
            title = await page.title()
            viewport = page.viewport_size
            
            # HTTP status (try to get from page)
            http_status = 200  # Default
            try:
                response = await page.evaluate("() => window.performance?.getEntriesByType?.('navigation')?.[0]?.responseStatus || 200")
                http_status = int(response) if response else 200
            except:
                pass
            
            # Antibot detection (basic, will enhance in BLOCK 5)
            antibot = await self._detect_antibot_basic(page)
            
            # Build elements array from DOM + Vision
            elements = await self._build_elements(dom_data, vision_elements)
            
            # Hints
            hints = await self._extract_hints(page)
            
            scene = {
                "viewport": [viewport['width'], viewport['height']],
                "url": url,
                "title": title,
                "http": {
                    "status": http_status,
                    "retry_after_ms": 0
                },
                "antibot": antibot,
                "elements": elements,
                "hints": hints,
                "ts": int(time.time() * 1000),
                "session_id": session_id
            }
            
            logger.info(f"📸 Scene built: {len(elements)} elements, antibot={antibot['present']}")
            return scene
            
        except Exception as e:
            logger.error(f"Scene build error: {e}")
            return self._get_fallback_scene(session_id)
    
    async def _detect_antibot_basic(self, page: Page) -> Dict[str, Any]:
        """Basic antibot detection (enhanced in BLOCK 5)"""
        try:
            # Check for common antibot indicators
            selectors = [
                'iframe[src*="recaptcha"]',
                'iframe[src*="hcaptcha"]',
                '.g-recaptcha',
                '.h-captcha',
                '[class*="cf-browser-verification"]',
                '[class*="cloudflare"]'
            ]
            
            for selector in selectors:
                el = await page.query_selector(selector)
                if el:
                    antibot_type = 'captcha' if 'captcha' in selector else 'cf_js_challenge'
                    provider = 'recaptcha' if 'recaptcha' in selector else 'hcaptcha' if 'hcaptcha' in selector else 'cloudflare'
                    
                    return {
                        "present": True,
                        "type": antibot_type,
                        "provider": provider,
                        "severity": 0.7,
                        "message": f"{provider} detected"
                    }
            
            # Check for rate limiting indicators
            page_text = await page.evaluate("() => document.body?.innerText || ''")
            if any(word in page_text.lower() for word in ['rate limit', 'too many requests', '429', 'slow down']):
                return {
                    "present": True,
                    "type": "rate_limit",
                    "provider": "unknown",
                    "severity": 0.5,
                    "message": "Rate limit detected"
                }
            
            return {
                "present": False,
                "type": "none",
                "provider": "none",
                "severity": 0.0,
                "message": ""
            }
            
        except Exception as e:
            logger.warning(f"Antibot detection error: {e}")
            return {
                "present": False,
                "type": "none",
                "provider": "none",
                "severity": 0.0,
                "message": ""
            }
    
    async def _build_elements(
        self, 
        dom_data: Dict[str, Any], 
        vision_elements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Build elements array from DOM + Vision
        Priority: DOM > Vision
        """
        elements = []
        element_id = 1
        
        # Process DOM clickables (PRIMARY)
        dom_clickables = dom_data.get('clickables', [])
        for dom_el in dom_clickables:
            bbox = dom_el.get('bbox', {})
            element = {
                "id": f"e{element_id}",
                "role": self._normalize_role(dom_el.get('type', 'node')),
                "label": dom_el.get('label', '')[:64],  # Limit label length
                "bbox": [
                    int(bbox.get('x', 0)),
                    int(bbox.get('y', 0)),
                    int(bbox.get('x', 0) + bbox.get('w', 0)),
                    int(bbox.get('y', 0) + bbox.get('h', 0))
                ],
                "state": {
                    "visible": True,
                    "enabled": True
                },
                "value": "",
                "confidence": dom_el.get('confidence', 0.85),
                "source": "dom"
            }
            elements.append(element)
            element_id += 1
        
        # Add vision-only elements (supplement)
        for vis_el in vision_elements:
            bbox = vis_el.get('bbox', {})
            # Check if not already in DOM elements (avoid duplicates)
            is_duplicate = False
            vis_x = bbox.get('x', 0)
            vis_y = bbox.get('y', 0)
            
            for existing in elements:
                ex_bbox = existing['bbox']
                if abs(ex_bbox[0] - vis_x) < 20 and abs(ex_bbox[1] - vis_y) < 20:
                    is_duplicate = True
                    break
            
            if not is_duplicate and vis_el.get('label'):
                element = {
                    "id": f"e{element_id}",
                    "role": self._normalize_role(vis_el.get('type', 'node')),
                    "label": vis_el.get('label', '')[:64],
                    "bbox": [
                        int(bbox.get('x', 0)),
                        int(bbox.get('y', 0)),
                        int(bbox.get('x', 0) + bbox.get('w', 0)),
                        int(bbox.get('y', 0) + bbox.get('h', 0))
                    ],
                    "state": {
                        "visible": True,
                        "enabled": True
                    },
                    "value": "",
                    "confidence": vis_el.get('confidence', 0.6),
                    "source": "vision"
                }
                elements.append(element)
                element_id += 1
        
        logger.info(f"Built {len(elements)} elements ({len(dom_clickables)} DOM, {len(elements) - len(dom_clickables)} vision)")
        return elements
    
    def _normalize_role(self, element_type: str) -> str:
        """Normalize element type to standard roles"""
        role_map = {
            'a': 'link',
            'button': 'button',
            'input': 'textbox',
            'textarea': 'textbox',
            'select': 'combobox',
            'img': 'image',
            'special': 'button',
            'node': 'element'
        }
        return role_map.get(element_type.lower(), 'element')
    
    async def _extract_hints(self, page: Page) -> Dict[str, Any]:
        """Extract page hints (lang, dialogs, captcha, etc.)"""
        try:
            hints = {
                "lang": "en",
                "dialogs": 0,
                "captcha": False,
                "loading": False
            }
            
            # Detect language
            lang = await page.evaluate("() => document.documentElement.lang || 'en'")
            hints['lang'] = lang[:10]
            
            # Count visible dialogs
            dialogs = await page.query_selector_all('[role="dialog"]:visible, .modal:visible, .dialog:visible')
            hints['dialogs'] = len(dialogs) if dialogs else 0
            
            # Captcha presence
            captcha_selectors = ['iframe[src*="captcha"]', '.g-recaptcha', '.h-captcha']
            for sel in captcha_selectors:
                if await page.query_selector(sel):
                    hints['captcha'] = True
                    break
            
            # Loading indicators
            loading_selectors = ['[class*="loading"]:visible', '[class*="spinner"]:visible']
            for sel in loading_selectors:
                if await page.query_selector(sel):
                    hints['loading'] = True
                    break
            
            return hints
            
        except Exception as e:
            logger.warning(f"Hints extraction error: {e}")
            return {"lang": "en", "dialogs": 0, "captcha": False, "loading": False}
    
    def _get_fallback_scene(self, session_id: str) -> Dict[str, Any]:
        """Fallback scene on error"""
        return {
            "viewport": [1280, 800],
            "url": "about:blank",
            "title": "Error",
            "http": {"status": 500, "retry_after_ms": 0},
            "antibot": {"present": False, "type": "none", "provider": "none", "severity": 0.0, "message": ""},
            "elements": [],
            "hints": {"lang": "en", "dialogs": 0, "captcha": False, "loading": False},
            "ts": int(time.time() * 1000),
            "session_id": session_id
        }

# Global instance
scene_builder_service = SceneBuilderService()
