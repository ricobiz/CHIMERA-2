import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PageStateService:
    async def detect(self, page) -> Dict[str, Any]:
        try:
            # Quick DOM checks for captcha frames
            captcha = False
            try:
                if await page.query_selector('iframe[src*="recaptcha"], iframe[src*="hcaptcha"], .g-recaptcha, .h-captcha, [class*="captcha"], #captcha'):
                    captcha = True
            except Exception:
                pass

            # Body text scan
            body_text = ''
            try:
                body_text = (await page.inner_text('body'))[:8000].lower()
            except Exception:
                body_text = ''

            def has_any(substrs):
                return any(s in body_text for s in substrs)

            if captcha:
                return {"state": "captcha"}
            if has_any(["phone", "телефон", "verify your phone", "phone number", "sms", "verification code"]):
                # Distinguish sms_code vs phone_request lightly
                if has_any(["verification code", "sms code", "enter the code", "код подтверждения"]):
                    return {"state": "sms_code"}
                return {"state": "phone_request"}
            if has_any(["account created", "welcome", "thanks for signing up", "добро пожаловать", "аккаунт создан"]):
                return {"state": "success"}
            return {"state": "unknown"}
        except Exception as e:
            logger.warning(f"detect page state error: {e}")
            return {"state": "unknown"}

page_state_service = PageStateService()
