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
from motor.motor_asyncio import AsyncIOMotorClient
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["lovable"])

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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

@router.post("/export")
async def export_project(request: dict):
    """Export project as ZIP file"""
    import zipfile
    import io
    from fastapi.responses import StreamingResponse
    
    try:
        code = request.get("code", "")
        project_name = request.get("project_name", "lovable-app")
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add main App file
            zip_file.writestr(f"{project_name}/src/App.jsx", code)
            
            # Add package.json
            package_json = """{
  "name": "%s",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "browserslist": {
    "production": [
      ">0.2%%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}""" % project_name
            zip_file.writestr(f"{project_name}/package.json", package_json)
            
            # Add index.html
            index_html = """<!DOCTYPE html>
<html lang="en">


@router.post("/validate-visual")
async def validate_visual(request: dict):
    """Validate generated UI visually using screenshot"""
    from services.visual_validator_service import visual_validator_service
    
    try:
        screenshot_base64 = request.get("screenshot")
        user_request = request.get("user_request")
        validator_model = request.get("validator_model", "anthropic/claude-3-haiku")
        
        if not screenshot_base64 or not user_request:
            raise HTTPException(status_code=400, detail="Missing screenshot or user_request")
        
        logger.info(f"Visual validation requested with model: {validator_model}")
        
        result = await visual_validator_service.validate_screenshot(
            screenshot_base64=screenshot_base64,
            user_request=user_request,
            model=validator_model
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in visual validation endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>%s</title>
    <script src="https://cdn.tailwindcss.com"></script>
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>""" % project_name
            zip_file.writestr(f"{project_name}/public/index.html", index_html)
            
            # Add README
            readme = f"""# {project_name}

Generated by Lovable Studio

## Installation

```bash
npm install
npm start
```

Open [http://localhost:3000](http://localhost:3000) to view it in the browser.
"""
            zip_file.writestr(f"{project_name}/README.md", readme)
        
        zip_buffer.seek(0)
        
        return StreamingResponse(
            io.BytesIO(zip_buffer.getvalue()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={project_name}.zip"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """Get a specific project by ID"""
    try:
        project = await db.projects.find_one({"id": project_id})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Update last accessed time
        await db.projects.update_one(
            {"id": project_id},
            {"$set": {"last_accessed": datetime.utcnow()}}
        )
        
        return Project(**project)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    try:
        result = await db.projects.delete_one({"id": project_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"message": "Project deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))