from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
from services.ai_memory_service import memory_service

router = APIRouter(prefix="/api/memory", tags=["memory"])
logger = logging.getLogger(__name__)

# ============= Request Models =============

class RememberFactRequest(BaseModel):
    fact: str
    category: str = "general"
    importance: float = 0.5

class RememberAutomationRequest(BaseModel):
    task_description: str
    steps: List[Dict]
    result: str
    success: bool

class RememberConversationRequest(BaseModel):
    user_message: str
    assistant_response: str
    session_id: str
    important: bool = False

class RecallRequest(BaseModel):
    query: str
    memory_type: str = "all"  # "user", "automation", "conversation", or "all"
    n_results: int = 5

class ExtractFactsRequest(BaseModel):
    messages: List[Dict[str, str]]
    session_id: str

class ChangeNameRequest(BaseModel):
    new_name: str


# ============= Endpoints =============

@router.post("/remember/fact")
async def remember_fact(request: RememberFactRequest):
    """Remember a fact about the user"""
    try:
        memory_id = await memory_service.remember_user_fact(
            request.fact,
            request.category,
            request.importance
        )
        return {"memory_id": memory_id, "message": "Fact remembered"}
    except Exception as e:
        logger.error(f"Error remembering fact: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remember/automation")
async def remember_automation(request: RememberAutomationRequest):
    """Remember an automation task"""
    try:
        await memory_service.remember_automation(
            request.task_description,
            request.steps,
            request.result,
            request.success
        )
        return {"message": "Automation remembered"}
    except Exception as e:
        logger.error(f"Error remembering automation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remember/conversation")
async def remember_conversation(request: RememberConversationRequest):
    """Remember important conversation moment"""
    try:
        await memory_service.remember_conversation(
            request.user_message,
            request.assistant_response,
            request.session_id,
            request.important
        )
        return {"message": "Conversation moment remembered"}
    except Exception as e:
        logger.error(f"Error remembering conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recall")
async def recall_memories(request: RecallRequest):
    """Recall relevant memories"""
    try:
        memories = await memory_service.recall(
            request.query,
            request.memory_type,
            request.n_results
        )
        return {"memories": memories}
    except Exception as e:
        logger.error(f"Error recalling memories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-facts")
async def extract_facts(request: ExtractFactsRequest):
    """Extract important facts from conversation"""
    try:
        facts = await memory_service.extract_facts_from_conversation(
            request.messages,
            request.session_id
        )
        return {"facts": facts, "count": len(facts)}
    except Exception as e:
        logger.error(f"Error extracting facts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/personality")
async def get_personality():
    """Get AI agent personality info"""
    try:
        memory_service.update_interaction_count()
        return {
            "personality": memory_service.personality,
            "stats": memory_service.get_stats()
        }
    except Exception as e:
        logger.error(f"Error getting personality: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/personality/change-name")
async def change_ai_name(request: ChangeNameRequest):
    """Allow AI to change its own name"""
    try:
        message = memory_service.change_name(request.new_name)
        return {"message": message, "new_name": request.new_name}
    except Exception as e:
        logger.error(f"Error changing name: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/greeting")
async def get_greeting():
    """Get personalized greeting"""
    try:
        greeting = await memory_service.get_personalized_greeting()
        return {"greeting": greeting}
    except Exception as e:
        logger.error(f"Error getting greeting: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/{prompt}")
async def get_context(prompt: str, n_memories: int = 3):
    """Get relevant context from memory for a prompt"""
    try:
        context = await memory_service.get_context_for_prompt(prompt, n_memories)
        return {"context": context}
    except Exception as e:
        logger.error(f"Error getting context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    """Get memory system statistics"""
    try:
        stats = memory_service.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
