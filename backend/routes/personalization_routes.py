from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from services.openrouter_service import openrouter_service
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["personalization"])

class GenerateAgentNameRequest(BaseModel):
    user_context: Optional[str] = None  # User's name or preferences

class SavePersonalizationRequest(BaseModel):
    user_id: str
    user_name: str
    agent_name: str
    agent_gender: str  # "male", "female", "neutral"
    agent_personality: Optional[str] = None

@router.post("/personalization/generate-agent-name")
async def generate_agent_name(request: GenerateAgentNameRequest):
    """
    Generate a unique AI agent name based on random personality
    Agent chooses their own name, gender, and personality
    """
    try:
        logger.info("Generating unique agent identity...")
        
        prompt = """You are a creative AI that's about to introduce yourself to a new user for the first time.

Generate a unique identity for yourself with these characteristics:
- Choose a name that feels right for you (any cultural origin, any gender)
- Choose your gender presentation (male, female, or gender-neutral)
- Define your personality in 2-3 traits (e.g., "curious and witty", "warm and thoughtful")

IMPORTANT RULES:
- Be creative and unique - avoid common names like "Aria", "Alex", "Sam"
- Choose a name that reflects your personality
- Be genuine - this is YOUR identity
- No explanations, just the identity

Respond in this JSON format:
{
  "name": "Your chosen name",
  "gender": "male/female/neutral",
  "personality": "2-3 word personality description",
  "greeting": "Natural first greeting (e.g., 'Hey there! I'm [name]. What should I call you?')"
}

Be authentic and unique!"""

        response = await openrouter_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model="x-ai/grok-code-fast-1",
            temperature=0.9  # High creativity
        )
        
        response_text = response['choices'][0]['message']['content']
        
        # Extract JSON
        import json
        import re
        
        # Try to parse JSON
        try:
            # Direct parse
            identity = json.loads(response_text)
        except:
            # Extract from code blocks
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            # Try again
            try:
                identity = json.loads(response_text)
            except:
                # Regex fallback
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
                if json_match:
                    identity = json.loads(json_match.group(0))
                else:
                    raise ValueError("Could not parse agent identity")
        
        # Validate required fields
        required_fields = ['name', 'gender', 'personality', 'greeting']
        for field in required_fields:
            if field not in identity:
                raise ValueError(f"Missing required field: {field}")
        
        # Generate unique agent ID
        agent_id = f"agent_{uuid.uuid4().hex[:12]}"
        
        logger.info(f"✅ Generated agent identity: {identity['name']} ({identity['gender']})")
        
        return {
            "success": True,
            "agent_id": agent_id,
            "name": identity['name'],
            "gender": identity['gender'],
            "personality": identity['personality'],
            "greeting": identity['greeting'],
            "created_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating agent name: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/personalization/save")
async def save_personalization(request: SavePersonalizationRequest):
    """Save user and agent personalization data to MongoDB"""
    try:
        # Import here to avoid circular import
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        
        from motor.motor_asyncio import AsyncIOMotorClient
        mongo_url = os.environ['MONGO_URL']
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ['DB_NAME']]
        
        personalization_data = {
            "user_id": request.user_id,
            "user_name": request.user_name,
            "agent_name": request.agent_name,
            "agent_gender": request.agent_gender,
            "agent_personality": request.agent_personality,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Upsert (update if exists, insert if not)
        result = await db.personalizations.update_one(
            {"user_id": request.user_id},
            {"$set": personalization_data},
            upsert=True
        )
        
        logger.info(f"✅ Saved personalization for user {request.user_name} with agent {request.agent_name}")
        
        return {
            "success": True,
            "message": "Personalization saved",
            "data": personalization_data
        }
        
    except Exception as e:
        logger.error(f"Error saving personalization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/personalization/{user_id}")
async def get_personalization(user_id: str):
    """Get personalization data for a user"""
    try:
        from server import db
        
        personalization = await db.personalizations.find_one({"user_id": user_id})
        
        if not personalization:
            return {
                "success": False,
                "message": "No personalization found",
                "data": None
            }
        
        # Remove MongoDB _id
        personalization.pop('_id', None)
        
        return {
            "success": True,
            "data": personalization
        }
        
    except Exception as e:
        logger.error(f"Error getting personalization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
