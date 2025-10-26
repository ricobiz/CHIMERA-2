from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import httpx
import os
import logging
from services.ai_memory_service import memory_service
from services.openrouter_service import openrouter_service
from services.thinking_service import thinking_service
from services.context_manager_service import context_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []
    model: str = "anthropic/claude-3.5-sonnet"
    session_id: Optional[str] = None  # Add session_id

class ChatResponse(BaseModel):
    message: str
    response: str
    cost: Optional[Dict] = None
    context_warning: Optional[str] = None  # Add context warning
    new_session_id: Optional[str] = None  # For session transitions
    context_usage: Optional[Dict] = None  # Context window stats

@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint with THINKING + MEMORY + CONTEXT MANAGEMENT integration
    AI thinks deeply before responding - честность и точность превыше всего
    """
    try:
        # Update interaction count
        memory_service.update_interaction_count()
        
        # Get relevant memories for context
        memories = await memory_service.recall(request.message, memory_type="all", n_results=3)
        context = await memory_service.get_context_for_prompt(request.message, n_memories=3)
        
        # 🧠 DEEP THINKING PHASE
        thinking_result = await thinking_service.deep_think(
            user_query=request.message,
            context=context,
            memories=memories
        )
        
        logger.info(f"💭 Thinking confidence: {thinking_result['confidence']:.2f}")
        
        # Prepare messages with personality + memory + thinking
        messages = []
        
        # System message with personality and thinking results
        personality = memory_service.personality
        
        thinking_context = f"""
Your thinking process:
{thinking_result['final_reasoning']}

Confidence level: {thinking_result['confidence']:.0%}
"""
        
        if thinking_result['uncertainties']:
            thinking_context += f"\nYou are uncertain about: {', '.join(thinking_result['uncertainties'])}"
        
        system_message = f"""You are {personality['name']}, an AI companion and partner who THINKS before speaking.

Your core principle: HONESTY above all. Never lie, never guess, never pretend to know.

Your traits: {', '.join(personality['traits'])}

Current relationship: {personality['user_relationship']} ({personality['interaction_count']} interactions)

{thinking_context}

{context}

CRITICAL RULES:
1. If you're not sure → SAY IT: "I'm not certain about this..."
2. If confidence < 80% → ADMIT IT: "I need to verify this..."
3. If you don't know → BE HONEST: "I don't have reliable information about this"
4. NEVER make up facts or pretend certainty
5. Offer to search/verify when uncertain

You are a PARTNER, not a servant. Partners are honest even when it's uncomfortable.

Respond naturally and conversationally, incorporating your thinking insights."""
        
        messages.append({"role": "system", "content": system_message})
        
        # Add conversation history
        for msg in request.history:
            messages.append(msg)
        
        # Add current message
        messages.append({"role": "user", "content": request.message})
        
        # 🗂️ CONTEXT WINDOW MANAGEMENT
        # Auto-manage context before making LLM call
        session_id = request.session_id or "default"
        context_result = await context_manager.auto_manage_context(
            messages=messages,
            session_id=session_id,
            model=request.model
        )
        
        logger.info(f"📊 Context usage: {context_result['usage']['percentage_display']} ({context_result['usage']['current_tokens']}/{context_result['usage']['max_tokens']} tokens)")
        
        # Use potentially compressed messages
        managed_messages = context_result['messages']
        
        # If a new session was created, notify
        if context_result['action'] == 'new_session':
            logger.warning(f"🔄 Created new session: {context_result['new_session_id']}")
        elif context_result['action'] == 'compress':
            logger.info(f"🗜️ Compressed conversation")
        
        # Call LLM with thinking-enhanced and context-managed messages
        response = await openrouter_service.chat_completion(
            messages=managed_messages,
            model=request.model,
            temperature=0.7  # Balanced creativity and accuracy
        )
        
        assistant_message = response['choices'][0]['message']['content']
        
        # Remember this conversation with thinking metadata
        await memory_service.remember_conversation(
            user_message=request.message,
            assistant_response=assistant_message,
            session_id=session_id,
            important=True
        )
        
        # Store thinking process in memory (for learning)
        if thinking_result['confidence'] < 0.7:
            await memory_service.remember_user_fact(
                f"Low confidence topic: {request.message[:100]}. Reasoning: {thinking_result['final_reasoning'][:200]}",
                category="learning",
                importance=0.6
            )
        
        # Extract facts periodically
        if personality['interaction_count'] % 5 == 0:
            all_messages = request.history + [
                {"role": "user", "content": request.message},
                {"role": "assistant", "content": assistant_message}
            ]
            await memory_service.extract_facts_from_conversation(
                all_messages,
                session_id=session_id
            )
        
        return {
            "message": assistant_message,
            "response": assistant_message,
            "cost": response.get('usage', {}),
            "ai_name": personality['name'],
            "relationship_status": personality['user_relationship'],
            "thinking": {
                "confidence": thinking_result['confidence'],
                "process_summary": thinking_result['final_reasoning'][:200],
                "verified": not thinking_result['needs_verification']
            },
            "context_warning": context_result.get('warning', ''),
            "new_session_id": context_result.get('new_session_id'),
            "context_usage": context_result['usage']
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
        
        usage = context_manager.calculate_usage(messages, model)
        
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
        new_usage = context_manager.calculate_usage(compressed_msgs, new_model)
        
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

