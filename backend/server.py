from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List
import uuid
from datetime import datetime, timezone


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

# Include the router in the main app
app.include_router(api_router)

# Include Lovable routes
from routes.lovable_routes import router as lovable_router
from routes.openrouter_models import router as models_router
from routes.session_routes import router as session_router
from routes.system_status import router as system_router
from routes.chat_routes import router as chat_router
from routes.integrations_routes import router as integrations_router
from routes.automation_routes import router as automation_router
from routes.memory_routes import router as memory_router
from routes.planning_routes import router as planning_router
from routes.document_verification_routes import router as doc_verify_router
from routes.self_improvement_routes import router as self_improve_router
from routes.hook_routes import router as hook_router
from routes.proxy_routes import router as proxy_router
from routes.personalization_routes import router as personalization_router
app.include_router(lovable_router)
app.include_router(models_router)
app.include_router(session_router)
app.include_router(system_router)
app.include_router(chat_router)
app.include_router(integrations_router)
app.include_router(automation_router)
app.include_router(memory_router)
app.include_router(planning_router)
app.include_router(doc_verify_router)
app.include_router(self_improve_router)
app.include_router(hook_router)
app.include_router(proxy_router)
app.include_router(personalization_router)

# Validation endpoint for browser automation
from pydantic import BaseModel as PydanticBaseModel
from services.visual_validator_service import visual_validator_service

class ValidationRequest(PydanticBaseModel):
    screenshot: str
    expectedUrl: str
    currentUrl: str
    pageTitle: str
    description: str

@app.post("/api/validate-navigation")
async def validate_navigation_endpoint(request: ValidationRequest):
    """Validate navigation success using vision API"""
    try:
        result = await visual_validator_service.validate_navigation(
            screenshot_base64=request.screenshot,
            expected_url=request.expectedUrl,
            current_url=request.currentUrl,
            page_title=request.pageTitle,
            description=request.description
        )
        return result
    except Exception as e:
        logger.error(f"Error validating navigation: {str(e)}")
        return {"success": False, "confidence": 0.2, "issues": [str(e)], "suggestions": ["Retry navigation"]}

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()