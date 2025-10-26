from fastapi import APIRouter, HTTPException
import os
import logging
import httpx

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["system"])

@router.get("/system-status")
async def get_system_status():
    """Check system status: API key validity and account balance"""
    try:
        api_key = os.environ.get('OPENROUTER_API_KEY')
        
        if not api_key:
            return {
                "status": "error",
                "message": "OpenRouter API key not configured",
                "has_key": False,
                "balance": None,
                "key_valid": False
            }
        
        # Check API key validity and get balance
        async with httpx.AsyncClient() as client:
            # Get account credits
            try:
                response = await client.get(
                    "https://openrouter.ai/api/v1/auth/key",
                    headers={
                        "Authorization": f"Bearer {api_key}"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    balance = data.get('data', {}).get('limit_remaining')
                    
                    return {
                        "status": "ok",
                        "message": "System operational",
                        "has_key": True,
                        "key_valid": True,
                        "balance": balance,
                        "currency": "USD"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Invalid API key",
                        "has_key": True,
                        "key_valid": False,
                        "balance": None
                    }
                    
            except httpx.TimeoutException:
                return {
                    "status": "warning",
                    "message": "OpenRouter API timeout",
                    "has_key": True,
                    "key_valid": None,
                    "balance": None
                }
            except Exception as e:
                logger.error(f"Error checking OpenRouter status: {str(e)}")
                return {
                    "status": "error",
                    "message": f"API check failed: {str(e)}",
                    "has_key": True,
                    "key_valid": False,
                    "balance": None
                }
                
    except Exception as e:
        logger.error(f"Error in system status check: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "has_key": False,
            "key_valid": False,
            "balance": None
        }
