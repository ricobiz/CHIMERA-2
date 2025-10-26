from fastapi import APIRouter, HTTPException
from typing import List
import logging
from datetime import datetime, timedelta

from models import Session, SessionListItem, Message
from motor.motor_asyncio import AsyncIOMotorClient
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["sessions"])

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

@router.post("/sessions", response_model=Session)
async def create_session(session: Session):
    """Create a new session"""
    try:
        await db.sessions.insert_one(session.dict())
        logger.info(f"Session created: {session.id}")
        return session
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions", response_model=List[SessionListItem])
async def get_sessions():
    """Get all sessions"""
    try:
        sessions = await db.sessions.find().sort("updated_at", -1).to_list(100)
        
        result = []
        for sess in sessions:
            # Calculate time ago
            updated_at = sess.get('updated_at', datetime.utcnow())
            time_diff = datetime.utcnow() - updated_at
            
            if time_diff < timedelta(hours=1):
                time_ago = f"{int(time_diff.total_seconds() / 60)} min ago"
            elif time_diff < timedelta(days=1):
                time_ago = f"{int(time_diff.total_seconds() / 3600)} hours ago"
            else:
                time_ago = f"{int(time_diff.days)} days ago"
            
            result.append(SessionListItem(
                id=sess['id'],
                name=sess.get('name', 'New Session'),
                message_count=len(sess.get('messages', [])),
                last_updated=time_ago,
                total_cost=sess.get('total_cost', 0.0)
            ))
        
        return result
    except Exception as e:
        logger.error(f"Error fetching sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}", response_model=Session)
async def get_session(session_id: str):
    """Get a specific session by ID"""
    try:
        session = await db.sessions.find_one({"id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Update last accessed time
        await db.sessions.update_one(
            {"id": session_id},
            {"$set": {"updated_at": datetime.utcnow()}}
        )
        
        return Session(**session)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/sessions/{session_id}", response_model=Session)
async def update_session(session_id: str, session_update: dict):
    """Update a session"""
    try:
        session_update['updated_at'] = datetime.utcnow()
        
        result = await db.sessions.update_one(
            {"id": session_id},
            {"$set": session_update}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Session not found")
        
        updated_session = await db.sessions.find_one({"id": session_id})
        return Session(**updated_session)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    try:
        result = await db.sessions.delete_one({"id": session_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
