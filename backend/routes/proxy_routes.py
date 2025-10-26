from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from services.proxy_service import proxy_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["proxy"])

@router.get("/proxy/status")
async def get_proxy_status() -> Dict[str, Any]:
    """Get current proxy service status"""
    try:
        if not proxy_service.is_enabled():
            return {
                "enabled": False,
                "message": "Proxy service not configured (no API key)"
            }
        
        # Fetch proxies if not already cached
        proxies = await proxy_service.get_proxies()
        
        return {
            "enabled": True,
            "total_proxies": len(proxies),
            "current_index": proxy_service.current_proxy_index,
            "last_fetch": proxy_service.last_fetch_time.isoformat() if proxy_service.last_fetch_time else None,
            "proxies": [
                {
                    "server": p['server'],
                    "country": p.get('country', 'Unknown')
                }
                for p in proxies[:5]  # Show first 5
            ]
        }
    except Exception as e:
        logger.error(f"Error getting proxy status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/proxy/rotate")
async def rotate_proxy() -> Dict[str, Any]:
    """Force proxy rotation"""
    try:
        if not proxy_service.is_enabled():
            raise HTTPException(status_code=400, detail="Proxy service not enabled")
        
        next_proxy = proxy_service.get_next_proxy()
        
        if not next_proxy:
            raise HTTPException(status_code=404, detail="No proxies available")
        
        return {
            "success": True,
            "proxy": {
                "server": next_proxy['server'],
                "country": next_proxy.get('country', 'Unknown')
            },
            "index": proxy_service.current_proxy_index,
            "total": proxy_service.get_proxy_count()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rotating proxy: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/proxy/refresh")
async def refresh_proxy_list() -> Dict[str, Any]:
    """Force refresh of proxy list from Webshare.io"""
    try:
        if not proxy_service.is_enabled():
            raise HTTPException(status_code=400, detail="Proxy service not enabled")
        
        proxies = await proxy_service.fetch_proxy_list()
        
        return {
            "success": True,
            "total_proxies": len(proxies),
            "message": f"Fetched {len(proxies)} proxies from Webshare.io"
        }
    except Exception as e:
        logger.error(f"Error refreshing proxy list: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
