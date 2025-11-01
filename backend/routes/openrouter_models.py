from fastapi import APIRouter, HTTPException
import os
import logging
import httpx

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["openrouter"]) 

@router.get("/models")
async def get_models():
    """Get list of available OpenRouter models from their API"""
    try:
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenRouter API key not configured")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://openrouter.ai/api/v1/models",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": os.environ.get("OPENROUTER_HTTP_REFERER", "https://lovable.studio"),
                    "X-Title": os.environ.get("OPENROUTER_X_TITLE", "Lovable Studio"),
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch models")
            
            data = response.json()
            models = data.get('data', [])
            
            # Process all models
            all_models = []
            for model in models:
                model_id = model.get('id', '')
                pricing = model.get('pricing', {})
                architecture = model.get('architecture', {})
                
                # Get modality info
                modality = architecture.get('modality', 'text->text')
                
                # Better vision detection
                has_vision = (
                    'image' in modality.lower() or
                    'vision' in model_id.lower() or
                    'vision' in model.get('name', '').lower() or
                    'multimodal' in modality.lower() or
                    'nano-banana' in model_id.lower() or
                    (model.get('name', '') and any(keyword in model.get('name', '').lower() for keyword in ['vision', 'image', 'multimodal', 'visual']))
                )
                
                # Normalize pricing numbers (fallback to 0)
                try:
                    prompt_price = float(pricing.get('prompt', '0') or 0)
                except Exception:
                    prompt_price = 0.0
                try:
                    completion_price = float(pricing.get('completion', '0') or 0)
                except Exception:
                    completion_price = 0.0
                try:
                    image_price = float(pricing.get('image', '0') or 0)
                except Exception:
                    image_price = 0.0

                all_models.append({
                    'id': model_id,
                    'name': model.get('name', model_id),
                    'description': model.get('description', '')[:300] + '...' if len(model.get('description', '')) > 300 else model.get('description', ''),
                    'context_length': model.get('context_length', 0),
                    'pricing': {
                        'prompt': prompt_price,
                        'completion': completion_price,
                        'image': image_price
                    },
                    'top_provider': model.get('top_provider', {}),
                    'architecture': architecture,
                    'modality': modality,
                    'capabilities': {
                        'tools': 'tool' in modality.lower() or 'function' in str(model).lower(),
                        'vision': has_vision,
                        'streaming': True
                    }
                })
            
            # Sort by pricing (free first, then by prompt price)
            all_models.sort(key=lambda x: (x['pricing']['prompt'], x['pricing']['completion']))
            
            logger.info(f"Fetched {len(all_models)} models from OpenRouter")
            return {"models": all_models}
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/openrouter/balance")
async def get_openrouter_balance():
    """Return OpenRouter account remaining balance (credits)"""
    try:
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenRouter API key not configured")
        
        async with httpx.AsyncClient() as client:
            # Try to get prepaid credits first (for prepaid accounts)
            try:
                credits_resp = await client.get(
                    "https://openrouter.ai/api/v1/credits",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=15.0
                )
                if credits_resp.status_code == 200:
                    credits_data = credits_resp.json()
                    data = credits_data.get('data', {})
                    total_credits = data.get('total_credits', 0)
                    total_usage = data.get('total_usage', 0)
                    
                    # Calculate remaining balance
                    remaining = total_credits - total_usage
                    
                    # Return with additional info
                    return {
                        "remaining": round(remaining, 2),
                        "currency": "USD",
                        "balance": round(remaining, 2),
                        "used": round(total_usage, 2),
                        "total_credits": round(total_credits, 2)
                    }
            except Exception as e:
                logger.warning(f"Credits endpoint failed, trying auth/key: {str(e)}")
            
            # Fallback to auth/key endpoint (for limit-based accounts)
            auth_resp = await client.get(
                "https://openrouter.ai/api/v1/auth/key",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=15.0
            )
            
            if auth_resp.status_code != 200:
                logger.error(f"OpenRouter balance error: {auth_resp.status_code} - {auth_resp.text}")
                raise HTTPException(status_code=auth_resp.status_code, detail="Failed to fetch balance")
            
            data = auth_resp.json()
            api_data = data.get('data', {})
            
            # Check if limit-based account
            limit = api_data.get('limit')
            limit_remaining = api_data.get('limit_remaining')
            usage = api_data.get('usage', 0)
            
            if limit is not None and limit_remaining is not None:
                # Limit-based account
                remaining = limit_remaining
            elif limit is None:
                # Unlimited/prepaid account without explicit balance
                # Return usage info instead
                remaining = None
            else:
                remaining = -1
            
            return {
                "remaining": remaining,
                "currency": "USD",
                "balance": remaining,
                "used": round(usage, 2) if usage else 0
            }
            
    except Exception as e:
        logger.error(f"Error fetching OpenRouter balance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/openrouter/overview")
async def get_openrouter_overview():
    """Combined endpoint: returns models list and current balance"""
    try:
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenRouter API key not configured")
        
        async with httpx.AsyncClient() as client:
            # Parallel requests
            models_req = client.get(
                "https://openrouter.ai/api/v1/models",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": os.environ.get("OPENROUTER_HTTP_REFERER", "https://lovable.studio"),
                    "X-Title": os.environ.get("OPENROUTER_X_TITLE", "Lovable Studio"),
                },
                timeout=30.0
            )
            balance_req = client.get(
                "https://openrouter.ai/api/v1/auth/key",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=15.0
            )
            import asyncio
            models_resp, balance_resp = await asyncio.gather(models_req, balance_req)

            if models_resp.status_code != 200:
                logger.error(f"OpenRouter models error: {models_resp.status_code} - {models_resp.text}")
                raise HTTPException(status_code=models_resp.status_code, detail="Failed to fetch models")
            if balance_resp.status_code != 200:
                logger.warning(f"OpenRouter balance warning: {balance_resp.status_code} - {balance_resp.text}")
                # proceed with balance = None
                balance_data = None
            else:
                balance_data = balance_resp.json()
            
            data = models_resp.json()
            models = data.get('data', [])

            formatted_models = []
            for model in models:
                model_id = model.get('id', '')
                pricing = model.get('pricing', {})
                architecture = model.get('architecture', {})
                modality = architecture.get('modality', 'text->text')
                has_vision = (
                    'image' in modality.lower() or
                    'vision' in model_id.lower() or
                    'vision' in model.get('name', '').lower() or
                    'multimodal' in modality.lower() or
                    'nano-banana' in model_id.lower() or
                    (model.get('name', '') and any(keyword in model.get('name', '').lower() for keyword in ['vision', 'image', 'multimodal', 'visual']))
                )
                try:
                    prompt_price = float(pricing.get('prompt', '0') or 0)
                except Exception:
                    prompt_price = 0.0
                try:
                    completion_price = float(pricing.get('completion', '0') or 0)
                except Exception:
                    completion_price = 0.0
                try:
                    image_price = float(pricing.get('image', '0') or 0)
                except Exception:
                    image_price = 0.0

                formatted_models.append({
                    'id': model_id,
                    'name': model.get('name', model_id),
                    'description': model.get('description', ''),
                    'context_length': model.get('context_length', 0),
                    'pricing': {
                        'prompt': prompt_price,
                        'completion': completion_price,
                        'image': image_price,
                    },
                    'capabilities': {
                        'vision': has_vision,
                        'tools': 'tool' in modality.lower() or 'function' in str(model).lower(),
                        'streaming': True,
                    },
                    'architecture': architecture,
                    'modality': modality,
                })

            formatted_models.sort(key=lambda x: (x['pricing']['prompt'], x['pricing']['completion']))
            
            # Try to get balance from credits endpoint
            balance_info = None
            try:
                credits_resp = await client.get(
                    "https://openrouter.ai/api/v1/credits",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=15.0
                )
                if credits_resp.status_code == 200:
                    credits_data = credits_resp.json()
                    data = credits_data.get('data', {})
                    total_credits = data.get('total_credits', 0)
                    total_usage = data.get('total_usage', 0)
                    remaining = total_credits - total_usage
                    balance_info = {
                        "remaining": round(remaining, 2),
                        "currency": "USD",
                        "balance": round(remaining, 2),
                        "used": round(total_usage, 2),
                        "total_credits": round(total_credits, 2)
                    }
            except Exception as e:
                logger.warning(f"Credits endpoint failed in overview: {str(e)}")
                # Fallback to balance_data from auth/key
                if balance_data:
                    api_data = balance_data.get('data', {})
                    remaining = api_data.get('limit_remaining')
                    balance_info = {
                        "remaining": remaining,
                        "currency": "USD",
                        "balance": remaining,
                        "used": round(api_data.get('usage', 0), 2)
                    }
            
            return {"models": formatted_models, "balance": balance_info}

    except Exception as e:
        logger.error(f"Error building OpenRouter overview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
