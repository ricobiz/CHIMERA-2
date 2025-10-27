import os
import json
import uuid
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from services.anti_detect import AntiDetectFingerprint, HumanBehaviorSimulator
from services.browser_automation_service import browser_service
from services.proxy_service import proxy_service

logger = logging.getLogger(__name__)

PROFILES_DIR = "/app/runtime/profiles"

class ProfileService:
    def __init__(self):
        os.makedirs(PROFILES_DIR, exist_ok=True)

    def _profile_path(self, profile_id: str) -> str:
        return os.path.join(PROFILES_DIR, profile_id)

    def _meta_path(self, profile_id: str) -> str:
        return os.path.join(self._profile_path(profile_id), "meta.json")

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

    async def _warmup(self, session_id: str, profile: Dict[str, Any]) -> None:
        try:
            urls = [
                "https://www.youtube.com/",
                "https://www.reddit.com/",
                "https://www.amazon.com/",
                "https://www.cnn.com/"
            ]
            page = browser_service.sessions[session_id]['page']
            for url in urls:
                await browser_service.navigate(session_id, url)
                # random scrolls and mouse moves
                for _ in range(3):
                    await HumanBehaviorSimulator.human_move(page, 50, 50)  # small nudge
                    await asyncio.sleep(0.5)
                    await page.mouse.wheel(0, 400)
                    await asyncio.sleep(1.0)
                await asyncio.sleep(1.0)
        except Exception as e:
            logger.warning(f"Warmup error: {e}")

    async def create_profile(self, region: Optional[str] = None, proxy_tier: Optional[str] = None) -> Dict[str, Any]:
        profile_id = str(uuid.uuid4())
        profile_dir = self._profile_path(profile_id)
        os.makedirs(profile_dir, exist_ok=True)

        # Generate fingerprint
        fingerprint = AntiDetectFingerprint.generate_profile(region=region)

        # Pick proxy
        proxy = proxy_service.get_proxy_by(region=region, tier=proxy_tier) if hasattr(proxy_service, 'get_proxy_by') else None

        # Launch persistent context as a session linked to this profile
        session_id = f"sess-{profile_id[:8]}"
        await browser_service.create_session_from_profile(profile_id=profile_id, session_id=session_id, fingerprint=fingerprint, proxy=proxy)

        # Warmup
        await self._warmup(session_id, fingerprint)

        # Save meta
        meta = {
            "profile_id": profile_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_used": datetime.now(timezone.utc).isoformat(),
            "used_count": 1,
            "region": region,
            "proxy_tier": proxy_tier,
            "proxy": proxy or {},
            "is_warm": True,
            "fingerprint": fingerprint,
        }
        self.write_meta(profile_id, meta)

        # Close session after warmup to flush data
        await browser_service.close_session(session_id)

        # Return summary
        summary = {
            "user_agent": fingerprint.get('user_agent'),
            "locale": fingerprint.get('locale'),
            "timezone": fingerprint.get('timezone_id'),
            "viewport": fingerprint.get('viewport'),
            "screen": fingerprint.get('screen'),
        }
        return {"profile_id": profile_id, "fingerprint_summary": summary}

    async def use_profile(self, profile_id: str) -> Dict[str, Any]:
        if not self.profile_exists(profile_id):
            raise ValueError("Profile not found")
        meta = self.read_meta(profile_id)
        fingerprint = meta.get('fingerprint', {})
        proxy = meta.get('proxy', None)
        session_id = f"sess-{profile_id[:8]}-{uuid.uuid4().hex[:4]}"
        await browser_service.create_session_from_profile(profile_id=profile_id, session_id=session_id, fingerprint=fingerprint, proxy=proxy)
        # Fast sanity navigate
        await browser_service.navigate(session_id, "https://www.google.com")

        # Update meta
        meta['last_used'] = datetime.now(timezone.utc).isoformat()
        meta['used_count'] = int(meta.get('used_count', 0)) + 1
        self.write_meta(profile_id, meta)
        return {"session_id": session_id}

    def status(self, profile_id: str) -> Dict[str, Any]:
        if not self.profile_exists(profile_id):
            raise ValueError("Profile not found")
        meta = self.read_meta(profile_id)
        return {
            "profile_id": profile_id,
            "region": meta.get('region'),
            "proxy_tier": meta.get('proxy_tier'),
            "proxy": meta.get('proxy'),
            "created_at": meta.get('created_at'),
            "last_used": meta.get('last_used'),
            "used_count": meta.get('used_count', 0),
            "is_warm": meta.get('is_warm', False)
        }

profile_service = ProfileService()
