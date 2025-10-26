"""
AI Agent Memory System with Personality
Векторная память для долгосрочного обучения и персонализации
"""
import logging
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os
import hashlib

logger = logging.getLogger(__name__)

class AIMemoryService:
    """
    Векторная память AI агента
    Сохраняет важную информацию из каждой сессии
    Персонализирует взаимодействие с пользователем
    """
    
    def __init__(self):
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path="/app/backend/data/chroma_db",
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding model (local, free!)
        logger.info("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # 80MB, very fast
        logger.info("✓ Embedding model loaded")
        
        # Collections
        self.user_memory = self.chroma_client.get_or_create_collection(
            name="user_memory",
            metadata={"description": "User preferences, facts, and personal info"}
        )
        
        self.automation_history = self.chroma_client.get_or_create_collection(
            name="automation_history",
            metadata={"description": "Past automation tasks and learnings"}
        )
        
        self.conversation_context = self.chroma_client.get_or_create_collection(
            name="conversation_context",
            metadata={"description": "Important conversation moments"}
        )
        
        # AI Agent personality
        self.personality_file = "/app/backend/data/ai_personality.json"
        self.personality = self.load_or_create_personality()
    
    def load_or_create_personality(self) -> Dict[str, Any]:
        """Load AI personality or create new one"""
        os.makedirs(os.path.dirname(self.personality_file), exist_ok=True)
        
        if os.path.exists(self.personality_file):
            with open(self.personality_file, 'r') as f:
                personality = json.load(f)
                logger.info(f"✓ Loaded AI personality: {personality['name']}")
                return personality
        
        # Create new AI personality
        personality = {
            "name": "Nova",  # Default name, can be changed
            "created_at": datetime.now().isoformat(),
            "traits": [
                "curious and always learning",
                "helpful and supportive partner",
                "remembers details about you",
                "grows smarter with each interaction",
                "creative problem solver"
            ],
            "core_values": [
                "Be a true companion, not just a tool",
                "Learn from every interaction",
                "Respect user privacy",
                "Always be honest and transparent"
            ],
            "interaction_count": 0,
            "last_interaction": None,
            "user_relationship": "new partnership"
        }
        
        self.save_personality(personality)
        logger.info(f"✓ Created new AI personality: {personality['name']}")
        return personality
    
    def save_personality(self, personality: Dict[str, Any]):
        """Save AI personality to disk"""
        with open(self.personality_file, 'w') as f:
            json.dump(personality, f, indent=2)
    
    def update_interaction_count(self):
        """Update interaction counter"""
        self.personality['interaction_count'] += 1
        self.personality['last_interaction'] = datetime.now().isoformat()
        
        # Update relationship status based on interaction count
        count = self.personality['interaction_count']
        if count < 10:
            self.personality['user_relationship'] = "getting to know each other"
        elif count < 50:
            self.personality['user_relationship'] = "growing partnership"
        elif count < 200:
            self.personality['user_relationship'] = "trusted companions"
        else:
            self.personality['user_relationship'] = "deep understanding & friendship"
        
        self.save_personality(self.personality)
    
    def change_name(self, new_name: str):
        """Allow AI to change its own name"""
        old_name = self.personality['name']
        self.personality['name'] = new_name
        self.personality['name_changed_at'] = datetime.now().isoformat()
        self.save_personality(self.personality)
        logger.info(f"AI renamed itself: {old_name} → {new_name}")
        return f"I've chosen to be called {new_name} from now on! 🌟"
    
    async def remember_user_fact(
        self,
        fact: str,
        category: str = "general",
        importance: float = 0.5
    ) -> str:
        """
        Remember a fact about the user
        
        Args:
            fact: The information to remember (e.g., "User prefers dark theme")
            category: Type of fact (preferences, personal, work, hobby, etc.)
            importance: 0.0 to 1.0, how important this fact is
        
        Returns:
            Memory ID
        """
        memory_id = hashlib.md5(f"{fact}{datetime.now()}".encode()).hexdigest()
        
        # Generate embedding
        embedding = self.embedding_model.encode(fact).tolist()
        
        # Store in vector DB
        self.user_memory.add(
            ids=[memory_id],
            embeddings=[embedding],
            documents=[fact],
            metadatas=[{
                "category": category,
                "importance": importance,
                "timestamp": datetime.now().isoformat(),
                "access_count": 0
            }]
        )
        
        logger.info(f"💾 Remembered: {fact[:50]}...")
        return memory_id
    
    async def remember_automation(
        self,
        task_description: str,
        steps: List[Dict],
        result: str,
        success: bool
    ):
        """
        Remember an automation task for future reference
        """
        automation_id = hashlib.md5(f"{task_description}{datetime.now()}".encode()).hexdigest()
        
        # Create searchable summary
        summary = f"Task: {task_description}. Steps: {len(steps)}. Result: {result}"
        embedding = self.embedding_model.encode(summary).tolist()
        
        self.automation_history.add(
            ids=[automation_id],
            embeddings=[embedding],
            documents=[summary],
            metadatas=[{
                "task": task_description,
                "steps_count": len(steps),
                "success": success,
                "timestamp": datetime.now().isoformat(),
                "result": result[:200]  # Store truncated result
            }]
        )
        
        logger.info(f"💾 Remembered automation: {task_description[:50]}...")
    
    async def remember_conversation(
        self,
        user_message: str,
        assistant_response: str,
        session_id: str,
        important: bool = False
    ):
        """
        Remember important conversation moments
        """
        if not important:
            # Auto-detect importance (contains questions, personal info, decisions)
            importance_keywords = [
                'prefer', 'like', 'love', 'hate', 'always', 'never',
                'my', 'I am', 'remember', 'important', 'please'
            ]
            important = any(kw in user_message.lower() for kw in importance_keywords)
        
        if important:
            convo_id = hashlib.md5(f"{session_id}{datetime.now()}".encode()).hexdigest()
            
            convo_text = f"User: {user_message}\nAssistant: {assistant_response}"
            embedding = self.embedding_model.encode(convo_text).tolist()
            
            self.conversation_context.add(
                ids=[convo_id],
                embeddings=[embedding],
                documents=[convo_text],
                metadatas=[{
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "user_msg_length": len(user_message),
                    "important": important
                }]
            )
            
            logger.info(f"💾 Remembered conversation moment from session {session_id}")
    
    async def recall(
        self,
        query: str,
        memory_type: str = "all",
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Recall relevant memories based on query
        
        Args:
            query: What to search for
            memory_type: "user", "automation", "conversation", or "all"
            n_results: How many memories to return
        
        Returns:
            List of relevant memories with metadata
        """
        query_embedding = self.embedding_model.encode(query).tolist()
        
        all_results = []
        
        collections_to_search = []
        if memory_type in ["user", "all"]:
            collections_to_search.append(("user", self.user_memory))
        if memory_type in ["automation", "all"]:
            collections_to_search.append(("automation", self.automation_history))
        if memory_type in ["conversation", "all"]:
            collections_to_search.append(("conversation", self.conversation_context))
        
        for mem_type, collection in collections_to_search:
            try:
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results
                )
                
                if results['documents'][0]:
                    for i, doc in enumerate(results['documents'][0]):
                        all_results.append({
                            'type': mem_type,
                            'memory': doc,
                            'metadata': results['metadatas'][0][i],
                            'distance': results['distances'][0][i] if 'distances' in results else 0,
                            'id': results['ids'][0][i]
                        })
                        
                        # Update access count
                        collection.update(
                            ids=[results['ids'][0][i]],
                            metadatas=[{
                                **results['metadatas'][0][i],
                                'access_count': results['metadatas'][0][i].get('access_count', 0) + 1
                            }]
                        )
            except Exception as e:
                logger.error(f"Error searching {mem_type} memory: {str(e)}")
        
        # Sort by relevance (distance)
        all_results.sort(key=lambda x: x['distance'])
        
        logger.info(f"🔍 Recalled {len(all_results)} memories for query: '{query[:50]}'")
        
        return all_results[:n_results]
    
    async def extract_facts_from_conversation(
        self,
        messages: List[Dict[str, str]],
        session_id: str
    ) -> List[str]:
        """
        Extract important facts from conversation using LLM
        Called at end of session or periodically
        """
        # Filter user messages
        user_messages = [m['content'] for m in messages if m['role'] == 'user']
        
        if not user_messages:
            return []
        
        # Simple heuristic extraction (can be enhanced with LLM)
        facts = []
        
        for msg in user_messages:
            # Detect preferences
            if 'prefer' in msg.lower() or 'like' in msg.lower():
                facts.append(f"User preference: {msg[:100]}")
            
            # Detect personal info
            if any(word in msg.lower() for word in ['my name', 'i am', 'i work', 'i live']):
                facts.append(f"Personal info: {msg[:100]}")
            
            # Detect recurring patterns
            if 'always' in msg.lower() or 'usually' in msg.lower():
                facts.append(f"User pattern: {msg[:100]}")
        
        # Save extracted facts
        for fact in facts:
            await self.remember_user_fact(fact, category="auto_extracted", importance=0.7)
        
        return facts
    
    async def get_personalized_greeting(self) -> str:
        """
        Generate personalized greeting based on relationship and history
        """
        name = self.personality['name']
        count = self.personality['interaction_count']
        relationship = self.personality['user_relationship']
        
        if count == 0:
            return f"Hi! I'm {name}, your AI companion. I'm excited to learn and grow with you! 🌟"
        elif count < 5:
            return f"Hello again! I'm {name}, and I'm getting to know you better with each conversation. 😊"
        elif count < 20:
            return f"Hey! Great to see you. I'm {name}, and I'm learning so much from our partnership! ✨"
        else:
            return f"Welcome back, friend! I'm {name}, and I remember our journey together. What shall we create today? 🚀"
    
    async def get_context_for_prompt(self, user_prompt: str, n_memories: int = 3) -> str:
        """
        Get relevant context from memory to enhance AI response
        """
        memories = await self.recall(user_prompt, memory_type="all", n_results=n_memories)
        
        if not memories:
            return ""
        
        context_parts = []
        for mem in memories:
            context_parts.append(f"[Memory: {mem['memory']}]")
        
        context = "\n".join(context_parts)
        return f"\n\nRelevant memories:\n{context}\n"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            "ai_name": self.personality['name'],
            "interaction_count": self.personality['interaction_count'],
            "relationship_status": self.personality['user_relationship'],
            "user_facts": self.user_memory.count(),
            "automation_memories": self.automation_history.count(),
            "conversation_memories": self.conversation_context.count(),
            "total_memories": (
                self.user_memory.count() + 
                self.automation_history.count() + 
                self.conversation_context.count()
            )
        }
    
    async def cleanup_old_memories(self, days_old: int = 90):
        """Remove memories older than specified days (privacy feature)"""
        # Implementation for GDPR compliance
        pass


# Global instance
memory_service = AIMemoryService()
