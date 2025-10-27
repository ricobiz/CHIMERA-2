"""
Simple AI Memory Service - MongoDB-based without ML dependencies
Stores conversation context, user preferences, and session state
NO ChromaDB, NO embeddings, NO RAG - just simple key-value storage
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
import os

logger = logging.getLogger(__name__)

class SimpleMemoryService:
    """Simple memory service using only MongoDB - no ML dependencies"""
    
    def __init__(self):
        self.mongo_url = os.environ.get('MONGO_URL')
        self.db_name = os.environ.get('DB_NAME', 'test_database')
        self.client = None
        self.db = None
        
    async def initialize(self):
        """Initialize MongoDB connection using shared client"""
        if not self.client:
            # Use shared MongoDB connection from server
            from server import client as shared_client, db as shared_db
            self.client = shared_client
            self.db = shared_db
            logger.info("✅ Simple memory service initialized (using shared MongoDB client)")
    
    async def store_conversation(self, session_id: str, user_message: str, 
                                 assistant_message: str, metadata: Dict = None):
        """Store conversation in MongoDB"""
        try:
            await self.initialize()
            
            conversation_entry = {
                "session_id": session_id,
                "user_message": user_message,
                "assistant_message": assistant_message,
                "timestamp": datetime.utcnow(),
                "metadata": metadata or {}
            }
            
            await self.db.conversations.insert_one(conversation_entry)
            logger.info(f"💾 Stored conversation for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error storing conversation: {e}")
    
    async def get_recent_conversations(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Get recent conversations for context"""
        try:
            await self.initialize()
            
            cursor = self.db.conversations.find(
                {"session_id": session_id}
            ).sort("timestamp", -1).limit(limit)
            
            conversations = await cursor.to_list(length=limit)
            
            # Reverse to get chronological order
            conversations.reverse()
            
            return conversations
            
        except Exception as e:
            logger.error(f"Error getting conversations: {e}")
            return []
    
    async def store_user_preference(self, user_id: str, key: str, value: Any):
        """Store user preference"""
        try:
            await self.initialize()
            
            await self.db.user_preferences.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        f"preferences.{key}": value,
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            logger.info(f"💾 Stored preference {key} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error storing preference: {e}")
    
    async def get_user_preferences(self, user_id: str) -> Dict:
        """Get all user preferences"""
        try:
            await self.initialize()
            
            doc = await self.db.user_preferences.find_one({"user_id": user_id})
            
            if doc and 'preferences' in doc:
                return doc['preferences']
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting preferences: {e}")
            return {}
    
    async def store_session_state(self, session_id: str, state: Dict):
        """Store session state (current task, context, etc.)"""
        try:
            await self.initialize()
            
            await self.db.session_states.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "state": state,
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            logger.info(f"💾 Stored session state for {session_id}")
            
        except Exception as e:
            logger.error(f"Error storing session state: {e}")
    
    async def get_session_state(self, session_id: str) -> Optional[Dict]:
        """Get session state"""
        try:
            await self.initialize()
            
            doc = await self.db.session_states.find_one({"session_id": session_id})
            
            if doc and 'state' in doc:
                return doc['state']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting session state: {e}")
            return None
    
    async def clear_session(self, session_id: str):
        """Clear all data for a session"""
        try:
            await self.initialize()
            
            await self.db.conversations.delete_many({"session_id": session_id})
            await self.db.session_states.delete_one({"session_id": session_id})
            
            logger.info(f"🗑️ Cleared session {session_id}")
            
        except Exception as e:
            logger.error(f"Error clearing session: {e}")
    
    async def get_conversation_summary(self, session_id: str) -> str:
        """Get a simple summary of recent conversations"""
        try:
            conversations = await self.get_recent_conversations(session_id, limit=5)
            
            if not conversations:
                return "No previous conversations"
            
            summary_parts = []
            for conv in conversations:
                user_msg = conv.get('user_message', '')[:100]
                ai_msg = conv.get('assistant_message', '')[:100]
                summary_parts.append(f"User: {user_msg}... | AI: {ai_msg}...")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error getting summary: {e}")
            return "Error loading conversation history"

# Global instance
simple_memory_service = SimpleMemoryService()
