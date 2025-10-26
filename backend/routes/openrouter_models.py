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
            
            # Filter for code generation models and sort by popularity
            code_models = []
            for model in models:
                model_id = model.get('id', '')
                # Filter for relevant code generation models
                if any(keyword in model_id.lower() for keyword in ['claude', 'gpt', 'gemini', 'llama', 'qwen', 'codestral', 'deepseek', 'mistral']):
                    pricing = model.get('pricing', {})
                    code_models.append({
                        'id': model_id,
                        'name': model.get('name', model_id),
                        'description': model.get('description', ''),
                        'context_length': model.get('context_length', 0),
                        'pricing': {
                            'prompt': float(pricing.get('prompt', '0')),
                            'completion': float(pricing.get('completion', '0')),
                            'image': float(pricing.get('image', '0'))
                        },
                        'top_provider': model.get('top_provider', {}),
                        'architecture': model.get('architecture', {}),
                        'capabilities': {
                            'tools': model.get('architecture', {}).get('tokenizer') == 'Llama2' or 'claude' in model_id.lower() or 'gpt' in model_id.lower(),
                            'vision': 'vision' in model_id.lower() or model.get('architecture', {}).get('modality') == 'multimodal',
                            'streaming': True
                        }
                    })
            
            # Sort by pricing (cheaper first) and limit to top 20
            code_models.sort(key=lambda x: x['pricing']['prompt'])
            
            logger.info(f"Fetched {len(code_models)} models from OpenRouter")
            return {"models": code_models[:20]}
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))