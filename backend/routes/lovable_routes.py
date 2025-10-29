from fastapi import APIRouter, HTTPException
from typing import List
import logging
from datetime import datetime, timedelta

from models import (
    GenerateCodeRequest,
    GenerateCodeResponse,
    ProjectCreate,
    Project,
    ProjectListItem
)
from services.openrouter_service import openrouter_service
from services.design_generator_service import design_generator_service
from services.visual_validator_service import visual_validator_service
from services.research_planner_service import research_planner_service
from motor.motor_asyncio import AsyncIOMotorClient
import os
import httpx

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["lovable"])

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

@router.post("/generate-image")
async def generate_image(request: dict):
    """
    Generate image using Gemini 2.5 Flash Image (Nano Banana)
    Works in all chat modes - Chat, Code, Automation
    """
    try:
        prompt = request.get("prompt")
        model = request.get("model", "google/gemini-2.5-flash-image")
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        logger.info(f"🎨 [IMAGE GEN] Generating image with prompt: {prompt[:50]}...")
        logger.info(f"🎨 [IMAGE GEN] Model: {model}")
        
        # Use design_generator_service для генерации изображения
        # Просто передаем prompt как design_spec
        result = await design_generator_service.generate_visual_mockup(
            design_spec=prompt,
            user_request=prompt,
            model=model
        )
        
        if result.get('is_image'):
            logger.info(f"✅ [IMAGE GEN] Image generated successfully")
            return {
                "image_url": result.get('mockup_data'),
                "is_image": True,
                "cost": {
                    "total_cost": (result.get('usage', {}).get('total_tokens', 0) * 0.000001)  # Примерная цена
                }
            }
        else:
            logger.warning(f"⚠️ [IMAGE GEN] Failed to generate image")
            return {
                "error": result.get('error', 'Image generation failed'),
                "is_image": False,
                "text_response": result.get('mockup_data')
            }
            
    except Exception as e:
        logger.error(f"❌ [IMAGE GEN] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")

@router.post("/generate-code", response_model=GenerateCodeResponse)
async def generate_code(request: GenerateCodeRequest):
    """Generate code using OpenRouter AI"""
    try:
        logger.info(f"Received code generation request: {request.prompt[:50]}... with model: {request.model}")
        
        # Convert Pydantic models to dicts for OpenRouter service
        conversation_history = [msg.dict() for msg in request.conversation_history]
        
        result = await openrouter_service.generate_code(
            prompt=request.prompt,
            conversation_history=conversation_history,
            model=request.model
        )
        
        # Calculate cost based on usage
        cost = None
        if result.get("usage"):
            # Get model pricing - make a simple calculation
            # Default pricing if we can't fetch model info
            input_cost_per_1m = 3.0  # default $3/M
            output_cost_per_1m = 15.0  # default $15/M
            
            input_cost = (result["usage"]["prompt_tokens"] / 1_000_000) * input_cost_per_1m
            output_cost = (result["usage"]["completion_tokens"] / 1_000_000) * output_cost_per_1m
            total_cost = input_cost + output_cost
            
            cost = {
                "input_tokens": result["usage"]["prompt_tokens"],
                "output_tokens": result["usage"]["completion_tokens"],
                "total_tokens": result["usage"]["total_tokens"],
                "input_cost": round(input_cost, 6),
                "output_cost": round(output_cost, 6),
                "total_cost": round(total_cost, 6),
                "currency": "USD"
            }
        
        return GenerateCodeResponse(
            code=result["code"],
            message=result["message"],
            usage=result.get("usage"),
            cost=cost
        )
    except Exception as e:
        logger.error(f"Error in generate_code endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects", response_model=Project)
async def create_project(project: ProjectCreate):
    """Save a new project"""
    try:
        project_obj = Project(**project.dict())
        await db.projects.insert_one(project_obj.dict())
        logger.info(f"Project created: {project_obj.name}")
        return project_obj
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects", response_model=List[ProjectListItem])
async def get_projects():
    """Get all projects"""
    try:
        projects = await db.projects.find().sort("last_accessed", -1).to_list(100)
        
        result = []
        for proj in projects:
            # Calculate time ago
            last_accessed = proj.get('last_accessed', datetime.utcnow())
            time_diff = datetime.utcnow() - last_accessed
            
            if time_diff < timedelta(hours=1):
                time_ago = f"{int(time_diff.total_seconds() / 60)} minutes ago"
            elif time_diff < timedelta(days=1):
                time_ago = f"{int(time_diff.total_seconds() / 3600)} hours ago"
            else:
                time_ago = f"{int(time_diff.days)} days ago"
            
            result.append(ProjectListItem(
                id=proj['id'],
                name=proj['name'],
                description=proj['description'],
                last_accessed=time_ago,
                icon=proj.get('icon', '🚀')
            ))
        
        return result
    except Exception as e:
        logger.error(f"Error fetching projects: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-design")
async def generate_design(request: dict):
    """Generate design specification using vision model"""
    try:
        user_request = request.get("user_request")
        model = request.get("model")
        
        if not user_request:
            raise HTTPException(status_code=400, detail="user_request is required")
        
        result = await design_generator_service.generate_design(user_request, model)
        
        return {
            "design_spec": result["design_spec"],
            "usage": result.get("usage", {})
        }
    except Exception as e:
        logger.error(f"Error in generate-design endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-mockup")
async def generate_mockup(request: dict):
    """Generate visual mockup image from design specification"""
    try:
        design_spec = request.get("design_spec")
        user_request = request.get("user_request")
        model = request.get("model")
        
        if not design_spec:
            raise HTTPException(status_code=400, detail="design_spec is required")
        if not user_request:
            raise HTTPException(status_code=400, detail="user_request is required")
        
        result = await design_generator_service.generate_visual_mockup(
            design_spec, user_request, model
        )
        
        return {
            "mockup_data": result["mockup_data"],
            "design_spec": result["design_spec"],
            "usage": result.get("usage", {})
        }
    except Exception as e:
        logger.error(f"Error in generate-mockup endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/revise-design")
async def revise_design(request: dict):
    """Revise design based on user feedback"""
    try:
        current_design = request.get("current_design")
        revision_request = request.get("revision_request")
        model = request.get("model")
        
        if not current_design:
            raise HTTPException(status_code=400, detail="current_design is required")
        if not revision_request:
            raise HTTPException(status_code=400, detail="revision_request is required")
        
        result = await design_generator_service.revise_design(
            current_design, revision_request, model
        )
        
        return {
            "design_spec": result["design_spec"],
            "usage": result.get("usage", {})
        }
    except Exception as e:
        logger.error(f"Error in revise-design endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-visual")
async def validate_visual(request: dict):
    """Validate UI screenshot using vision model"""
    try:
        screenshot = request.get("screenshot")
        user_request = request.get("user_request")
        validator_model = request.get("validator_model", "anthropic/claude-3-haiku")
        
        if not screenshot:
            raise HTTPException(status_code=400, detail="screenshot is required")
        if not user_request:
            raise HTTPException(status_code=400, detail="user_request is required")
        
        # Remove data URL prefix if present
        if screenshot.startswith("data:image"):
            screenshot = screenshot.split(",")[1]
        
        result = await visual_validator_service.validate_screenshot(
            screenshot, 
            user_request,
            validator_model
        )
        
        return result
    except Exception as e:
        logger.error(f"Error in validate-visual endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/openrouter/balance")
async def get_openrouter_balance():
    """Get OpenRouter account balance"""
    try:
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenRouter API key not configured")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://openrouter.ai/api/v1/auth/key",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            response.raise_for_status()
            data = response.json()
            
            # OpenRouter returns credit information
            # Handle null values for unlimited accounts
            api_data = data.get("data", {})
            limit = api_data.get("limit")
            usage = api_data.get("usage", 0)
            limit_remaining = api_data.get("limit_remaining")
            
            return {
                "remaining": limit_remaining if limit_remaining is not None else -1,  # -1 indicates unlimited
                "currency": api_data.get("limit_unit", "USD"),
                "balance": limit if limit is not None else -1,  # -1 indicates unlimited
                "used": usage,
                "label": api_data.get("label", ""),
                "is_free_tier": api_data.get("is_free_tier", False)
            }
    except Exception as e:
        logger.error(f"Error fetching OpenRouter balance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/research-task")
async def research_task(request: dict):
    """
    Research Planner: Analyze task complexity and conduct research before development.
    Used for complex tasks to ensure current best practices are followed.
    """
    try:
        user_request = request.get("user_request")
        model = request.get("model")
        research_mode = request.get("research_mode", "full")  # 'analyze' or 'full'
        
        if not user_request:
            raise HTTPException(status_code=400, detail="user_request is required")
        
        if research_mode == "analyze":
            # Only analyze complexity, don't perform full research
            result = await research_planner_service.analyze_task_complexity(user_request, model)
        else:
            # Full research pipeline
            result = await research_planner_service.conduct_full_research(user_request, model)
        
        return result
    except Exception as e:
        logger.error(f"Error in research-task endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
