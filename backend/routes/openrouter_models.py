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
                    "HTTP-Referer": "https://lovable.studio",
                    "X-Title": "Lovable Studio"
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
                
                all_models.append({
                    'id': model_id,
                    'name': model.get('name', model_id),
                    'description': model.get('description', '')[:300] + '...' if len(model.get('description', '')) > 300 else model.get('description', ''),
                    'context_length': model.get('context_length', 0),
                    'pricing': {
                        'prompt': float(pricing.get('prompt', '0')),
                        'completion': float(pricing.get('completion', '0')),
                        'image': float(pricing.get('image', '0'))
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