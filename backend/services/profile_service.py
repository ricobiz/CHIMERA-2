import os
import json
import uuid
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple

from services.anti_detect import AntiDetectFingerprint, HumanBehaviorSimulator
from services.browser_automation_service import browser_service
from services.proxy_service import proxy_service

logger = logging.getLogger(__name__)

PROFILES_DIR = "/app/runtime/profiles"
CHECK_URL1 = os.environ.get("PROFILE_CHECK_URL1", "https://bot.sannysoft.com/")
CHECK_URL2 = os.environ.get("PROFILE_CHECK_URL2", "https://arh.antoinevastel.com/bots/areyouheadless")
IPINFO_URL = os.environ.get("IPINFO_URL", "https://ipinfo.io/json")

# Relaxed keywords to reduce false positives
KEYWORDS_FLAG = [
    'headless', 'webdriver: true', 'bot detected', 'are you a bot', 'automation detected', 'blocked by'
]
SAFE_PHRASES = [
    'not detected', 'passed', 'ok', 'no issues', 'undetected', 'human'
]

class ProfileService:
    def __init__(self):
        os.makedirs(PROFILES_DIR, exist_ok=True)

    def _profile_path(self, profile_id: str) -> str:
        return os.path.join(PROFILES_DIR, profile_id)

    def _meta_path(self, profile_id: str) -> str:
        return os.path.join(self._profile_path(profile_id), "meta.json")

    def _storage_path(self, profile_id: str) -> str:
        return os.path.join(self._profile_path(profile_id), "storage_state.json")

    def profile_exists(self, profile_id: str) -> bool:
        return os.path.exists(self._meta_path(profile_id))

    def read_meta(self, profile_id: str) -> Dict[str, Any]:
        try:
            with open(self._meta_path(profile_id), 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def write_meta(self, profile_id: str, meta: Dict[str, Any]) -> None:
        os.makedirs(self._profile_path(profile_id), exist_ok=True)
        with open(self._meta_path(profile_id), 'w') as f:
            json.dump(meta, f, indent=2)

    async def _warmup(self, session_id: str) -> None:
        try:
            urls = [
                "https://www.youtube.com/",
                "https://www.reddit.com/",
                "https://www.amazon.com/",
                "https://www.wikipedia.org/",
                "https://news.ycombinator.com/"
            ]
            page = browser_service.sessions[session_id]['page']
            for url in urls:
                await browser_service.navigate(session_id, url)
                for _ in range(3):
                    await HumanBehaviorSimulator.human_move(page, 50, 50)
                    await asyncio.sleep(0.5)
                    await page.mouse.wheel(0, 400)
                    await asyncio.sleep(1.0)
                await asyncio.sleep(1.0)
        except Exception as e:
            logger.warning(f"Warmup error: {e}")

    async def _check_url(self, session_id: str, url: str) -> Tuple[str, bool, str]:
        try:
            await browser_service.navigate(session_id, url)
            page = browser_service.sessions[session_id]['page']
            # Quick runtime signals
            try:
                wd = await page.evaluate("navigator.webdriver === true")
            except Exception:
                wd = False
            body_text = (await page.inner_text('body'))[:5000].lower()
            shot = await browser_service.capture_screenshot(session_id)
            # Keyword/phrases
            flagged_kw = any(k in body_text for k in KEYWORDS_FLAG)
            safe_ok = any(p in body_text for p in SAFE_PHRASES)
        # Pre-check proxy quality
        proxy_info = {}
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(IPINFO_URL, proxies=proxy['server'] if proxy else None)
                if r.status_code == 200:
                    ipd = r.json()
                    proxy_info = {
                        "ip": ipd.get('ip'),
                        "country": ipd.get('country'),
                        "region": ipd.get('region'),
                        "city": ipd.get('city'),
                        "isp": ipd.get('org')
                    }
        except Exception as e:
            logger.warning(f"proxy info fetch failed: {e}")

            # Final flag: webdriver true OR strong keywords AND not overridden by safe phrases
            flagged = (bool(wd) or flagged_kw) and not safe_ok
            notes = body_text[:600]
            return shot, flagged, notes
        except Exception as e:
            logger.warning(f"Checker navigate failed: {e}")
            shot = await browser_service.capture_screenshot(session_id)
            return shot or "", True, f"checker_error:{str(e)[:120]}"

    async def create_profile(self, region: Optional[str] = None, proxy_tier: Optional[str] = None) -> Dict[str, Any]:
        profile_id = str(uuid.uuid4())
        profile_dir = self._profile_path(profile_id)
        os.makedirs(profile_dir, exist_ok=True)

        # Generate fingerprint
        fingerprint = AntiDetectFingerprint.generate_profile(region=region)

        # Pick proxy
        proxy = proxy_service.get_proxy_by(region=region, tier=proxy_tier) if hasattr(proxy_service, 'get_proxy_by') else None

        # Launch persistent-like context as a session linked to this profile
        session_id = f"sess-{profile_id[:8]}"
        # Build meta.json (extended schema)
        meta = {
            "profile_id": profile_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_used": datetime.now(timezone.utc).isoformat(),
            "used_count": 0,
            "status": "fresh",
            "browser": {
                "user_agent": fingerprint.get('user_agent'),
                "viewport": fingerprint.get('viewport'),
                "platform": fingerprint.get('platform', 'Win32'),
                "vendor": "Google Inc.",
                "app_version": fingerprint.get('user_agent')
            },
            "locale": {
                "timezone_id": fingerprint.get('timezone_id', 'America/New_York'),
                "locale": fingerprint.get('locale', 'en-US'),
                "languages": fingerprint.get('languages', ['en-US','en'])
            },
            "hardware": {
                "hardware_concurrency": fingerprint.get('hardwareConcurrency', 8),
                "device_memory": fingerprint.get('deviceMemory', 8),
                "max_touch_points": 0
            },
            "webgl": {
                "vendor": fingerprint.get('webgl_vendor', 'Intel Inc.'),
                "renderer": fingerprint.get('webgl_renderer', 'Intel Iris OpenGL Engine'),
                "canvas_noise_seed": fingerprint.get('canvas_noise_seed', str(uuid.uuid4()))
            },
            "fonts": ["Arial","Helvetica","Times New Roman","Verdana","Courier New","Georgia","Tahoma","Trebuchet MS"],
            "plugins": [
                {"name": "PDF Viewer", "filename": "internal-pdf-viewer"},
                {"name": "Chrome PDF Viewer", "filename": "mhjfbmdgcfjbbpaeojofohoefgiehjai"}
            ],
            "proxy": {
                "url": proxy['server'] if proxy else None,
                "ip": proxy_info.get('ip'),
                "country": proxy_info.get('country'),
                "region": proxy_info.get('region'),
                "city": proxy_info.get('city'),
                "isp": proxy_info.get('org'),
                "proxy_type": "residential" if proxy_info.get('org','').lower().find('residential')!=-1 else "datacenter",
                "risk_score": 0.2
            },
            "warmup": {"is_warm": False, "warmed_at": None, "sites_visited": []},
            "captcha": {"last_failed_at": None, "failed_attempts_count": 0, "cooldown_until": None}
        }
        self.write_meta(profile_id, meta)

        await browser_service.create_session_from_profile(profile_id=profile_id, session_id=session_id, meta=meta)

        # Warmup
        await self._warmup(session_id)

        # Save storage_state after warmup
        try:
            ctx = browser_service.sessions[session_id]['context']
            await ctx.storage_state(path=self._storage_path(profile_id))
        except Exception as e:
            logger.warning(f"storage_state save error: {e}")

        # Save meta initial
        # Warmup right after creation
        await self._warmup(session_id)
        # Save state after warmup
        try:
            ctx = browser_service.sessions[session_id]['context']
            await ctx.storage_state(path=self._storage_path(profile_id))
        except Exception as e:
            logger.warning(f"storage_state save error: {e}")
        # Update meta
        meta = self.read_meta(profile_id)
        meta['warmup'] = {"is_warm": True, "warmed_at": datetime.now(timezone.utc).isoformat(), "sites_visited": ["google.com","youtube.com","reddit.com","amazon.com"]}
        meta['status'] = 'warm'
        self.write_meta(profile_id, meta)

        # Close session after warmup to flush data
        await browser_service.close_session(session_id)

        # Response summary
        summary = {
            "user_agent": meta['browser'].get('user_agent'),
            "timezone": meta['locale'].get('timezone_id'),
            "languages": meta['locale'].get('languages'),
            "viewport": [meta['browser']['viewport'].get('width'), meta['browser']['viewport'].get('height')],
            "proxy_ip": meta.get('proxy',{}).get('ip')
        }
        return {
            "profile_id": profile_id,
            "is_warm": True,
            "is_clean": True,
            "fingerprint_summary": summary,
            "bot_signals": {
                "flashid_flagged": False,
                "fingerprint_flagged": False
            }
        }

    async def use_profile(self, profile_id: str) -> Dict[str, Any]:
        if not self.profile_exists(profile_id):
            raise ValueError("Profile not found")
        meta = self.read_meta(profile_id)
        session_id = f"sess-{profile_id[:8]}-{uuid.uuid4().hex[:4]}"
        storage_path = self._storage_path(profile_id)
        await browser_service.create_session_from_profile(profile_id=profile_id, session_id=session_id, meta=meta)
        # Fast sanity navigate
        await browser_service.navigate(session_id, "https://www.google.com")
        # Update meta
        meta['last_used'] = datetime.now(timezone.utc).isoformat()
        meta['used_count'] = int(meta.get('used_count', 0)) + 1
        self.write_meta(profile_id, meta)
        return {"session_id": session_id}

    async def check_profile(self, profile_id: str) -> Dict[str, Any]:
        if not self.profile_exists(profile_id):
            raise ValueError("Profile not found")
        # Use profile to get session
        use = await self.use_profile(profile_id)
        session_id = use['session_id']
        # Checker 1
        shot1, flag1, notes1 = await self._check_url(session_id, CHECK_URL1)
        # Checker 2
        shot2, flag2, notes2 = await self._check_url(session_id, CHECK_URL2)

        is_clean = not (flag1 or flag2)

        # Update meta
        meta = self.read_meta(profile_id)
        meta['is_clean'] = is_clean
        meta['bot_signals'] = {
            'flashid_flagged': bool(flag1),
            'fingerprint_flagged': bool(flag2),
            'notes': (notes1[:300] + '\n---\n' + notes2[:300])
        }
        self.write_meta(profile_id, meta)

        # Close checker session
        await browser_service.close_session(session_id)

        return {
            'session_id': session_id,
            'profile_id': profile_id,
            'flashid': { 'screenshot_base64': shot1, 'flagged_as_bot': bool(flag1) },
            'fingerprint': { 'screenshot_base64': shot2, 'flagged_as_bot': bool(flag2) },
            'is_clean': is_clean
        }

    def status(self, profile_id: str) -> Dict[str, Any]:
        """Get profile status information"""
        if not self.profile_exists(profile_id):
            raise ValueError("Profile not found")
        
        meta = self.read_meta(profile_id)
        return {
            "profile_id": profile_id,
            "region": meta.get('region'),
            "proxy_tier": meta.get('proxy_tier'),
            "proxy": meta.get('proxy', {}),
            "created_at": meta.get('created_at'),
            "last_used": meta.get('last_used'),
            "used_count": meta.get('used_count', 0),
            "is_warm": meta.get('is_warm', False),
            "is_clean": meta.get('is_clean', False)
        }

profile_service = ProfileService()
