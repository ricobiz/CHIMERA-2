from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

class Message(BaseModel):
    role: str
    content: str

class GenerateCodeRequest(BaseModel):
    prompt: str
    conversation_history: List[Message] = []

class GenerateCodeResponse(BaseModel):
    code: str
    message: str
    conversation_id: Optional[str] = None

class ProjectCreate(BaseModel):
    name: str
    description: str = ''
    code: str = ''
    conversation_history: List[Message] = []

class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ''
    code: str = ''
    conversation_history: List[Message] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    icon: str = '🚀'

class ProjectListItem(BaseModel):
    id: str
    name: str
    description: str
    last_accessed: str
    icon: str