from pydantic import BaseModel, Field, validator
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
    total_cost: Optional[float] = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('total_cost', pre=True, always=True)
    def set_default_total_cost(cls, v):
        return v if v is not None else 0.0
    
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

# ============= Automation History Models =============

class StepResult(BaseModel):
    """Unified step result format"""
    success: bool
    confidence: float
    concerns: List[str] = []
    needs_human: bool = False
    step_name: str
    screenshot_after: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    details: Optional[dict] = {}

class ResultBundle(BaseModel):
    """Result bundle for completed missions"""
    credentials: Optional[dict] = {}
    proof: Optional[dict] = {}
    notes: Optional[str] = ""
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class AutomationHistory(BaseModel):
    """Automation mission history entry"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    job_id: str
    goal: str
    steps: List[StepResult] = []
    mission_status: str  # "completed" | "needs_human" | "failed" | "in_progress"
    human_help_reason: Optional[str] = None
    result_bundle: Optional[ResultBundle] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    class Config:
        populate_by_name = True
    project_name: str = "lovable-app"