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
            resp = await client.get(
                "https://openrouter.ai/api/v1/auth/key",
                headers={
                    "Authorization": f"Bearer {api_key}"
                },
                timeout=15.0
            )
            if resp.status_code != 200:
                logger.error(f"OpenRouter balance error: {resp.status_code} - {resp.text}")
                raise HTTPException(status_code=resp.status_code, detail="Failed to fetch balance")
            data = resp.json()
            remaining = data.get('data', {}).get('limit_remaining')
            currency = data.get('data', {}).get('limit_unit', 'USD')
            return {"remaining": remaining, "currency": currency}
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
            remaining = None
            if balance_data:
                remaining = balance_data.get('data', {}).get('limit_remaining')
            return {"models": formatted_models, "balance": remaining}

    except Exception as e:
        logger.error(f"Error building OpenRouter overview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
