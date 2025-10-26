from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

class Message(BaseModel):
    role: str
    content: str
    cost: Optional[dict] = None

class GenerateCodeRequest(BaseModel):
    prompt: str
    conversation_history: List[Message] = []
    model: Optional[str] = "anthropic/claude-3.5-sonnet"
    session_id: Optional[str] = None

class GenerateCodeResponse(BaseModel):
    code: str
    message: str
    conversation_id: Optional[str] = None
    usage: Optional[dict] = None
    cost: Optional[dict] = None
    session_id: Optional[str] = None

class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Session"
    messages: List[Message] = []
    generated_code: str = ""
    model_used: str = "anthropic/claude-3.5-sonnet"
    validator_model: Optional[str] = None
    validator_enabled: bool = False
    total_cost: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
class SessionListItem(BaseModel):
    id: str
    name: str
    message_count: int
    last_updated: str
    total_cost: float

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

class ExportRequest(BaseModel):
    code: str
    project_name: str = "lovable-app"