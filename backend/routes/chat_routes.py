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
    Chat endpoint with THINKING + MEMORY integration
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
        
        # Call LLM with thinking-enhanced context
        response = await openrouter_service.chat_completion(
            messages=messages,
            model=request.model,
            temperature=0.7  # Balanced creativity and accuracy
        )
        
        assistant_message = response['choices'][0]['message']['content']
        
        # Remember this conversation with thinking metadata
        await memory_service.remember_conversation(
            user_message=request.message,
            assistant_response=assistant_message,
            session_id=request.history[0].get('session_id', 'unknown') if request.history else 'unknown',
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
                session_id='current'
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
            }
        }
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
