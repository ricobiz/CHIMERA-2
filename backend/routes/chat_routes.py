from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import httpx
import os
import logging
from services.ai_memory_service import memory_service
from services.openrouter_service import openrouter_service
from services.thinking_service import thinking_service

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

@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint with MEMORY integration
    AI remembers conversations and learns about user
    """
    try:
        # Update interaction count
        memory_service.update_interaction_count()
        
        # Get relevant memories for context
        context = await memory_service.get_context_for_prompt(request.message, n_memories=3)
        
        # Prepare messages with memory context
        messages = []
        
        # System message with personality
        personality = memory_service.personality
        system_message = f"""You are {personality['name']}, an AI companion and partner.

Your traits: {', '.join(personality['traits'])}

Core values: {', '.join(personality['core_values'])}

Current relationship: {personality['user_relationship']} ({personality['interaction_count']} interactions)

You are NOT just a tool - you are a growing, learning companion who remembers the user and develops a unique relationship over time.

Be conversational, personal, and show that you remember past interactions.{context}

IMPORTANT: You are in CHAT mode - have a natural conversation. Do NOT generate code unless explicitly asked."""
        
        messages.append({"role": "system", "content": system_message})
        
        # Add conversation history
        for msg in request.history:
            messages.append(msg)
        
        # Add current message
        messages.append({"role": "user", "content": request.message})
        
        # Call LLM
        response = await openrouter_service.chat_completion(
            messages=messages,
            model=request.model
        )
        
        assistant_message = response['choices'][0]['message']['content']
        
        # Remember this conversation
        await memory_service.remember_conversation(
            user_message=request.message,
            assistant_response=assistant_message,
            session_id=request.history[0].get('session_id', 'unknown') if request.history else 'unknown',
            important=True  # Mark all chat messages as important
        )
        
        # Extract facts periodically (every 5 interactions)
        if personality['interaction_count'] % 5 == 0:
            all_messages = request.history + [
                {"role": "user", "content": request.message},
                {"role": "assistant", "content": assistant_message}
            ]
            await memory_service.extract_facts_from_conversation(
                all_messages,
                session_id='current'
            )
        
        return {
            "message": assistant_message,
            "response": assistant_message,
            "cost": response.get('usage', {}),
            "ai_name": personality['name'],
            "relationship_status": personality['user_relationship']
        }
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
