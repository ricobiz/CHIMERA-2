from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import httpx
import os
import logging
# from services.ai_memory_service import memory_service  # Disabled for MVP - will use external embedding API
from services.openrouter_service import openrouter_service
from services.thinking_service import thinking_service
from services.context_manager_service import context_manager
from services.task_classifier_service import task_classifier

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])

class TaskClassificationRequest(BaseModel):
    message: str
    model: str = "anthropic/claude-sonnet-4.5"  # Planning/conversation model

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []
    model: str = "anthropic/claude-sonnet-4.5"  # Planning/conversation model
    session_id: Optional[str] = None  # Add session_id

class ChatResponse(BaseModel):
    message: str
    response: str
    cost: Optional[Dict] = None
    context_warning: Optional[str] = None  # Add context warning
    new_session_id: Optional[str] = None  # For session transitions
    context_usage: Optional[Dict] = None  # Context window stats

@router.post("/classify-task")
async def classify_task(request: TaskClassificationRequest):
    """
    Classify user message to determine if it's:
    - browser_automation
    - code_generation
    - document_verification
    - general_chat
    """
    try:
        classification = await task_classifier.classify_task(
            user_message=request.message,
            model=request.model
        )
        
        return {
            "success": True,
            "classification": classification
        }
        
    except Exception as e:
        logger.error(f"Error in task classification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat(request: ChatRequest):
    """Chat endpoint with natural personality and personalization"""
    try:
        # Get personalization data if available
        agent_name = "an AI companion"
        user_name = "friend"
        agent_personality = "curious and helpful"
        
        if request.session_id:
            try:
                # Use shared DB connection from server
                from server import db
                
                personalization = await db.personalizations.find_one({"user_id": request.session_id})
                if personalization:
                    agent_name = personalization.get('agent_name', agent_name)
                    user_name = personalization.get('user_name', user_name)
                    agent_personality = personalization.get('agent_personality', agent_personality)
            except Exception as e:
                logger.warning(f"Could not load personalization: {e}")
                pass  # Continue without personalization
        
        # Build natural system message
        system_message = f"""You are {agent_name}, {agent_personality}.

You're having a natural conversation with {user_name}. Be genuine, creative, and helpful.

CRITICAL RULES:
1. NEVER say "How can I help you?" or "What can I do for you?" - that's robotic
2. NEVER mention you're an AI, assistant, or model - you're simply {agent_name}
3. Speak naturally like a real person having a conversation
4. Use casual language, contractions, natural flow
5. Show genuine interest and personality
6. When uncertain, say "I'm not sure" or "Let me think about that"
7. Be honest if you don't know something
8. React naturally to what {user_name} says
9. No formalities - be like a smart friend
10. Keep responses concise unless detail is needed

Examples of GOOD responses:
- "Oh that's interesting! Tell me more about..."
- "Hmm, let me think..."
- "I'd approach it this way..."
- "That reminds me of..."

Examples of BAD responses (NEVER use these):
- "How can I help you today?" ❌
- "As an AI assistant..." ❌
- "I'm here to help" ❌
- "What would you like me to do?" ❌

Just be {agent_name} - natural, genuine, and conversational."""
        
        # Build messages array
        messages = [{"role": "system", "content": system_message}]
        
        # Add conversation history
        for msg in request.history:
            messages.append(msg)
        
        # Add current message
        messages.append({"role": "user", "content": request.message})
        
        # Guard: ensure non-empty response from model; retry once if empty
        def is_empty_text(t: str) -> bool:
            if t is None:
                return True
            s = str(t).strip()
            if s == "" or s.lower() in ["null", "none", "undefined"]:
                return True
            return False

        # Call LLM with personalized system message
        response = await openrouter_service.chat_completion(
            messages=messages,
            model=request.model,
            temperature=0.8  # Higher creativity for natural conversation
        )
        
        assistant_message = response['choices'][0]['message']['content']
        if is_empty_text(assistant_message):
            logger.warning("Empty assistant response received; retrying once with lower temperature")
            # Retry once with lower temperature and short max_tokens
            response = await openrouter_service.chat_completion(
                messages=messages,
                model=request.model,
                temperature=0.3,
                max_tokens=512
            )
            assistant_message = response['choices'][0]['message']['content'] or ""
        if is_empty_text(assistant_message):
            assistant_message = "[No content returned by model]"
        
        return {
            "message": assistant_message,
            "response": assistant_message,
            "usage": response.get('usage', {}),
            "cost": response.get('usage', {}),
            "ai_name": agent_name,
            "user_name": user_name,
            "personality": agent_personality
        }
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.post("/context/status")
async def get_context_status(request: Dict):
    """
    Get current context window usage status
    """
    try:
        messages = request.get('history', [])
        model = request.get('model', 'anthropic/claude-3.5-sonnet')
        
        usage = await context_manager.calculate_usage(messages, model)
        
        return {
            "status": "success",
            "usage": usage,
            "warning": context_manager.format_context_warning(usage)
        }
    except Exception as e:
        logger.error(f"Context status error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get context status: {str(e)}")


@router.post("/context/switch-model")
async def switch_model_with_context(request: Dict):
    """
    Switch to a new model, creating a new session with preserved context
    """
    try:
        current_session_id = request.get('session_id', 'default')
        new_model = request.get('new_model')
        messages = request.get('history', [])
        old_model = request.get('old_model', 'anthropic/claude-3.5-sonnet')
        
        if not new_model:
            raise HTTPException(status_code=400, detail="new_model is required")
        
        logger.info(f"🔄 Switching from {old_model} to {new_model}")
        
        # Compress current conversation
        compressed_msgs, compression_info = await context_manager.compress_conversation(
            messages=messages,
            model=old_model,
            target_reduction=0.6
        )
        
        # Create new session with preserved context
        new_session = await context_manager.create_new_session_with_context(
            current_session_id=current_session_id,
            compressed_messages=compressed_msgs,
            compression_info=compression_info
        )
        
        # Calculate new context limits
        new_usage = await context_manager.calculate_usage(compressed_msgs, new_model)
        
        return {
            "status": "success",
            "new_session_id": new_session['session_id'],
            "parent_session_id": current_session_id,
            "compressed_messages": compressed_msgs,
            "compression_info": compression_info,
            "new_context_usage": new_usage,
            "message": f"Switched to {new_model}. New session created with preserved context."
        }
    except Exception as e:
        logger.error(f"Model switch error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to switch model: {str(e)}")

