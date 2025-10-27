"""
Simple Memory Routes - MongoDB-based without RAG/ML
Basic conversation history and session state storage
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
from services.simple_memory_service import simple_memory_service

router = APIRouter(prefix="/api/memory", tags=["memory"])
logger = logging.getLogger(__name__)

class StoreConversationRequest(BaseModel):
    session_id: str
    user_message: str
    assistant_message: str
    metadata: Optional[Dict] = None

class StorePreferenceRequest(BaseModel):
    user_id: str
    key: str
    value: Any

class StoreSessionStateRequest(BaseModel):
    session_id: str
    state: Dict

@router.post("/store-conversation")
async def store_conversation(request: StoreConversationRequest):
    """Store conversation in MongoDB for context"""
    try:
        await simple_memory_service.store_conversation(
            request.session_id,
            request.user_message,
            request.assistant_message,
            request.metadata
        )
        
        return {
            "success": True,
            "message": "Conversation stored"
        }
    except Exception as e:
        logger.error(f"Error storing conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{session_id}")
async def get_conversations(session_id: str, limit: int = 10):
    """Get recent conversations for a session"""
    try:
        conversations = await simple_memory_service.get_recent_conversations(session_id, limit)
        
        return {
            "success": True,
            "session_id": session_id,
            "conversations": conversations,
            "count": len(conversations)
        }
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversation-summary/{session_id}")
async def get_conversation_summary(session_id: str):
    """Get simple text summary of recent conversations"""
    try:
        summary = await simple_memory_service.get_conversation_summary(session_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/store-preference")
async def store_preference(request: StorePreferenceRequest):
    """Store user preference"""
    try:
        await simple_memory_service.store_user_preference(
            request.user_id,
            request.key,
            request.value
        )
        
        return {
            "success": True,
            "message": f"Preference {request.key} stored"
        }
    except Exception as e:
        logger.error(f"Error storing preference: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/preferences/{user_id}")
async def get_preferences(user_id: str):
    """Get all user preferences"""
    try:
        preferences = await simple_memory_service.get_user_preferences(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "preferences": preferences
        }
    except Exception as e:
        logger.error(f"Error getting preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/store-session-state")
async def store_session_state(request: StoreSessionStateRequest):
    """Store session state"""
    try:
        await simple_memory_service.store_session_state(
            request.session_id,
            request.state
        )
        
        return {
            "success": True,
            "message": "Session state stored"
        }
    except Exception as e:
        logger.error(f"Error storing session state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session-state/{session_id}")
async def get_session_state(session_id: str):
    """Get session state"""
    try:
        state = await simple_memory_service.get_session_state(session_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "state": state
        }
    except Exception as e:
        logger.error(f"Error getting session state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear all data for a session"""
    try:
        await simple_memory_service.clear_session(session_id)
        
        return {
            "success": True,
            "message": f"Session {session_id} cleared"
        }
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))
