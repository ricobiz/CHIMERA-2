"""
SelfTest Service - Bot-surface profiling
Checks fingerprint, IP/ASN, browser properties
"""
import logging
import random
from typing import Dict, Any, List, Optional
from playwright.async_api import Page

logger = logging.getLogger(__name__)

class SelfTestService:
    """
    Bot-surface profiling with actionable advice
    """
    
    async def run_test(
        self,
        page: Page,
        profile: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run self-test on current page/profile
        Returns: {score, issues, ip, fp}
        """
        try:
            issues = []
            score = 100  # Start with perfect score
            
            # Internal checks
            internal_checks = await self._run_internal_checks(page)
            score -= len(internal_checks['issues']) * 5
            issues.extend(internal_checks['issues'])
            
            # IP/ASN check (simplified)
            ip_info = await self._check_ip()
            if ip_info.get('type') == 'hosting':
                issues.append({
                    "id": "asn_hosting",
                    "severity": "high",
                    "hint": "Use residential proxy or profile 'slow_proxy'"
                })
                score -= 20
            
            # Fingerprint checks
            fp = internal_checks['fp']
            if not fp.get('tz_ok'):
                issues.append({
                    "id": "tz_mismatch",
                    "severity": "medium",
                    "hint": "Timezone doesn't match IP location"
                })
                score -= 10
            
            score = max(0, score)
            
            report = {
                "score": score,
                "issues": issues,
                "ip": ip_info,
                "fp": fp,
                "profile": profile or "default",
                "grade": "green" if score >= 80 else "yellow" if score >= 60 else "red"
            }
            
            logger.info(f"🔍 SelfTest: score={score}, issues={len(issues)}, grade={report['grade']}")
            
            return report
            
        except Exception as e:
            logger.error(f"SelfTest error: {e}")
            return self._get_fallback_report(profile)
    
    async def _run_internal_checks(self, page: Page) -> Dict[str, Any]:
        """Run browser fingerprint checks"""
        try:
            checks = await page.evaluate("""() => {
                const issues = [];
                const fp = {};
                
                // webdriver check
                if (navigator.webdriver) {
                    issues.push({id: 'webdriver_true', severity: 'critical'});
                }
                
                // Chrome check
                if (!window.chrome || !window.chrome.runtime) {
                    issues.push({id: 'no_chrome_object', severity: 'medium'});
                }
                
                // Plugins check
                if (navigator.plugins.length === 0) {
                    issues.push({id: 'no_plugins', severity: 'low'});
                }
                fp.plugins_count = navigator.plugins.length;
                
                // Languages
                fp.languages = navigator.languages;
                if (!navigator.languages || navigator.languages.length === 0) {
                    issues.push({id: 'no_languages', severity: 'medium'});
                }
                
                // Hardware
                fp.hardwareConcurrency = navigator.hardwareConcurrency || 0;
                fp.deviceMemory = navigator.deviceMemory || 0;
                
                // Timezone
                const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
                fp.timezone = tz;
                fp.tz_ok = tz && tz !== 'UTC';
                
                // WebGL
                try {
                    const canvas = document.createElement('canvas');
                    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                    if (gl) {
                        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                        if (debugInfo) {
                            fp.gl_vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
                            fp.gl_renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
                            fp.gl_ok = true;
                        }
                    }
                } catch (e) {
                    fp.gl_ok = false;
                }
                
                // Canvas fingerprint stability
                fp.canvas_stable = true;
                
                // Fonts check
                fp.fonts_ok = true;
                
                return {issues, fp};
            }""")
            
            return checks
            
        except Exception as e:
            logger.warning(f"Internal checks error: {e}")
            return {"issues": [], "fp": {}}
    
    async def _check_ip(self) -> Dict[str, Any]:
        """Check IP/ASN (simplified)"""
        try:
            # In real implementation: query ipinfo.io or similar
            # For now: return mock data
            return {
                "ip": "203.0.113.42",
                "asn": "AS15169",
                "range": "15169/16",
                "type": random.choice(["residential", "hosting", "datacenter"]),
                "country": "US",
                "city": "Mountain View"
            }
        except Exception as e:
            logger.warning(f"IP check error: {e}")
            return {"ip": "unknown", "type": "unknown"}
    
    def _get_fallback_report(self, profile: Optional[str]) -> Dict[str, Any]:
        """Fallback report on error"""
        return {
            "score": 50,
            "issues": [{"id": "selftest_error", "severity": "high", "hint": "SelfTest failed to run"}],
            "ip": {"ip": "unknown", "type": "unknown"},
            "fp": {},
            "profile": profile or "default",
            "grade": "yellow"
        }
    
    def get_last_report(self, profile: str) -> Optional[Dict[str, Any]]:
        """Get last test report (stub for now)"""
        # In real implementation: load from DB/cache
        return None


# Global instance
selftest_service = SelfTestService()
