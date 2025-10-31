"""
Autonomous Routes - API endpoints for autonomous automation
Provides new endpoints for the bulletproof automation system
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging

from automation import autonomous_agent
from .hook_routes import TaskRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/autonomous', tags=['autonomous'])

class AutonomousTaskRequest(BaseModel):
    goal: str
    context: Optional[Dict[str, Any]] = None
    user_data: Optional[Dict[str, Any]] = None

class AutonomousTaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

@router.post('/run', response_model=AutonomousTaskResponse)
async def run_autonomous_task(request: AutonomousTaskRequest):
    """
    Start autonomous task with bulletproof automation.
    Supports real-time WebSocket updates and comprehensive error handling.
    """
    try:
        # Setup WebSocket callback for real-time events
        events_log = []
        
        async def capture_events(event: Dict[str, Any]):
            events_log.append(event)
            logger.info(f"🔄 [AUTONOMOUS-API] {event['type']}: {event.get('data', {})}")
        
        # Configure autonomous agent
        autonomous_agent.ws_callback = capture_events
        
        # Default context
        context = request.context or {}
        default_context = {
            "timeout_minutes": 15,
            "max_retries": 3,
            "use_proxy": True,
            "solve_captcha": True
        }
        context.update(default_context)
        
        # Execute autonomous task
        result = await autonomous_agent.run(
            goal=request.goal,
            context=context,
            user_data=request.user_data
        )
        
        if result.get("status") == "SUCCESS":
            return AutonomousTaskResponse(
                task_id=result.get("task_id", "unknown"),
                status="SUCCESS",
                message="Task completed successfully"
            )
        elif result.get("status") == "NEEDS_USER_DATA":
            return AutonomousTaskResponse(
                task_id=result.get("task_id", "unknown"),
                status="NEEDS_USER_DATA", 
                message=result.get("message", "User data required")
            )
        else:
            return AutonomousTaskResponse(
                task_id=result.get("task_id", "unknown"),
                status="FAILED",
                message=result.get("reason", "Task failed")
            )
    
    except Exception as e:
        logger.error(f"❌ [AUTONOMOUS-API] Task execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/status/{task_id}')
async def get_task_status(task_id: str):
    """Get detailed status of autonomous task"""
    try:
        if autonomous_agent.task_id != task_id:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "task_id": task_id,
            "goal": autonomous_agent.current_goal,
            "state": autonomous_agent.state.value,
            "session_id": autonomous_agent.session_id,
            "progress": {
                "current_step": autonomous_agent.current_step_index,
                "total_steps": len(autonomous_agent.current_plan.get("steps", [])) if autonomous_agent.current_plan else 0,
                "completion_percentage": (autonomous_agent.current_step_index / max(1, len(autonomous_agent.current_plan.get("steps", [])))) * 100 if autonomous_agent.current_plan else 0
            },
            "resources": autonomous_agent.resources,
            "metrics": autonomous_agent.metrics,
            "execution_time": (autonomous_agent.start_time and (time.time() - autonomous_agent.start_time)) or 0,
            "stuck_count": autonomous_agent.stuck_count,
            "last_steps": autonomous_agent.execution_history[-5:] if autonomous_agent.execution_history else []
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [AUTONOMOUS-API] Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/stop/{task_id}')
async def stop_task(task_id: str):
    """Stop autonomous task execution"""
    try:
        if autonomous_agent.task_id != task_id:
            raise HTTPException(status_code=404, detail="Task not found")
        
        await autonomous_agent.stop()
        
        return {
            "task_id": task_id,
            "status": "STOPPED",
            "message": "Task stopped successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [AUTONOMOUS-API] Task stop failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/pause/{task_id}')
async def pause_task(task_id: str):
    """Pause autonomous task execution"""
    try:
        if autonomous_agent.task_id != task_id:
            raise HTTPException(status_code=404, detail="Task not found")
        
        await autonomous_agent.pause()
        
        return {
            "task_id": task_id,
            "status": "PAUSED",
            "message": "Task paused successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [AUTONOMOUS-API] Task pause failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/resume/{task_id}')
async def resume_task(task_id: str):
    """Resume paused autonomous task"""
    try:
        if autonomous_agent.task_id != task_id:
            raise HTTPException(status_code=404, detail="Task not found")
        
        await autonomous_agent.resume()
        
        return {
            "task_id": task_id,
            "status": "RESUMED",
            "message": "Task resumed successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [AUTONOMOUS-API] Task resume failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/tools')
async def get_available_tools():
    """Get list of available automation tools"""
    try:
        from automation.tools.orchestrator import tool_orchestrator
        
        tools = tool_orchestrator.get_available_tools()
        usage_stats = tool_orchestrator.get_tool_usage_stats()
        
        return {
            "available_tools": tools,
            "usage_statistics": usage_stats,
            "total_tools": len(tools)
        }
    
    except Exception as e:
        logger.error(f"❌ [AUTONOMOUS-API] Tools listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/tools/{tool_name}')
async def execute_tool(tool_name: str, params: Dict[str, Any] = None):
    """Execute specific automation tool"""
    try:
        from automation.tools.orchestrator import tool_orchestrator
        
        result = await tool_orchestrator.execute(tool_name, params or {})
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [AUTONOMOUS-API] Tool execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/metrics')
async def get_autonomous_metrics():
    """Get autonomous automation performance metrics"""
    try:
        if not autonomous_agent.start_time:
            return {
                "status": "idle",
                "message": "No active task"
            }
        
        return {
            "status": autonomous_agent.state.value,
            "metrics": autonomous_agent._calculate_metrics(),
            "performance": {
                "avg_step_time": autonomous_agent.metrics.get("execution_time", 0) / max(1, autonomous_agent.metrics.get("steps_completed", 1)),
                "success_rate": autonomous_agent.metrics.get("success_rate", 0),
                "retry_rate": autonomous_agent.metrics.get("retry_rate", 0),
                "tools_used": autonomous_agent.metrics.get("tools_used", 0)
            }
        }
    
    except Exception as e:
        logger.error(f"❌ [AUTONOMOUS-API] Metrics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/health')
async def health_check():
    """Health check for autonomous automation system"""
    try:
        # Check if all components are working
        from automation import meta_planner, tactical_brain, tool_orchestrator, perception, execution, verification
        
        health_status = {
            "autonomous_agent": autonomous_agent is not None,
            "meta_planner": meta_planner is not None,
            "tactical_brain": tactical_brain is not None,
            "tool_orchestrator": tool_orchestrator is not None,
            "perception": perception is not None,
            "execution": execution is not None,
            "verification": verification is not None
        }
        
        all_healthy = all(health_status.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "components": health_status,
            "message": "All systems operational" if all_healthy else "Some components unavailable"
        }
    
    except Exception as e:
        logger.error(f"❌ [AUTONOMOUS-API] Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }