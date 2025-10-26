from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import httpx
import os
import logging
from services.ai_memory_service import memory_service
from services.openrouter_service import openrouter_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []
    model: str = "anthropic/claude-3.5-sonnet"

class ChatResponse(BaseModel):
    message: str
    response: str
    cost: Optional[Dict] = None

@router.post("/chat", response_model=ChatResponse)
async def chat_conversation(request: ChatRequest):
    """
    Simple chat endpoint for conversational mode (no code generation).
    Used when user is in Chat mode to discuss app ideas and planning.
    """
    try:
        openrouter_api_key = os.environ.get('OPENROUTER_API_KEY')
        if not openrouter_api_key:
            raise HTTPException(status_code=500, detail="OpenRouter API key not configured")
        
        # Build conversation history
        messages = []
        for msg in request.history[-5:]:  # Last 5 messages for context
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        # Add system message for chat mode
        system_message = {
            "role": "system",
            "content": """You are a helpful AI assistant helping users plan and discuss their app ideas.

IMPORTANT: Always respond in the SAME LANGUAGE that the user writes in. If they write in Russian, respond in Russian. If they write in English, respond in English.

In Chat mode, you should:
- Have natural, friendly conversations
- Help brainstorm and refine app concepts
- Discuss features, user experience, and design ideas
- Answer questions about app development
- Provide suggestions and best practices
- Ask clarifying questions to better understand their needs

Be conversational and natural. Do NOT mention switching modes or technical details about the interface."""
        }
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": request.message
        })
        
        # Call OpenRouter API
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openrouter_api_key}",
                    "HTTP-Referer": "https://app.emergent.sh",
                    "X-Title": "Lovable Clone - Chat Mode"
                },
                json={
                    "model": request.model,
                    "messages": [system_message] + messages,
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            )
            
            response.raise_for_status()
            data = response.json()
            
            assistant_message = data['choices'][0]['message']['content']
            
            # Extract cost information
            usage = data.get('usage', {})
            cost_info = None
            if usage:
                # Rough cost calculation (adjust based on actual OpenRouter pricing)
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
                total_tokens = usage.get('total_tokens', prompt_tokens + completion_tokens)
                
                # Approximate cost (varies by model)
                cost_per_1k_prompt = 0.003
                cost_per_1k_completion = 0.015
                
                total_cost = (prompt_tokens / 1000 * cost_per_1k_prompt) + \
                            (completion_tokens / 1000 * cost_per_1k_completion)
                
                cost_info = {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "total_cost": total_cost
                }
            
            logger.info(f"Chat response generated. Tokens: {cost_info.get('total_tokens', 0) if cost_info else 0}")
            
            return ChatResponse(
                message=assistant_message,
                response=assistant_message,
                cost=cost_info
            )
            
    except httpx.HTTPError as e:
        logger.error(f"OpenRouter API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to communicate with AI: {str(e)}")
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
