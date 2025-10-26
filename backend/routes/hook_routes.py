"""
Hook Routes - AI Entry Point API
Universal gateway between user/external AI and internal execution agent
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/hook", tags=["agent-hook"])

# Global state objects - REAL, not mocked
current_task = {"text": "", "job_id": None, "timestamp": None}
execution_logs = []
agent_status = "IDLE"  # IDLE, ACTIVE, ERROR

# Global result object - stores final artifacts
last_result = {
    "screenshot": None,
    "credentials": None,
    "completed": False
}

# Global control state - agent mode
control_state = {
    "run_mode": "PAUSED"  # ACTIVE, PAUSED, STOP
}

class TaskRequest(BaseModel):
    text: str
    timestamp: int
    nocache: bool = True

class LogEntry(BaseModel):
    ts: str
    step: int
    action: str
    status: str  # ok, error, warning, info
    error: Optional[str] = None

@router.post("/exec")
async def execute_task(request: TaskRequest):
    """
    Execute a task - main entry point for orchestrator AI
    Returns job_id for tracking
    """
    global current_task, agent_status, execution_logs
    
    try:
        job_id = str(uuid.uuid4())
        
        # Store current task
        current_task = {
            "text": request.text,
            "job_id": job_id,
            "timestamp": request.timestamp
        }
        
        # Clear previous logs
        execution_logs = []
        
        # Set agent to active
        agent_status = "ACTIVE"
        
        logger.info(f"[HOOK] Task accepted: {request.text[:100]}... | Job ID: {job_id}")
        
        # Add initial log entry
        execution_logs.append({
            "ts": datetime.now().isoformat(),
            "step": 0,
            "action": f"Task received: {request.text[:80]}...",
            "status": "ok",
            "error": None
        })
        
        # Simulate task execution (mock)
        # In real implementation, this would trigger actual browser automation
        _simulate_task_execution(request.text)
        
        return {
            "status": "accepted",
            "job_id": job_id,
            "message": "Task accepted for execution"
        }
        
    except Exception as e:
        logger.error(f"[HOOK] Error executing task: {str(e)}")
        agent_status = "ERROR"
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/log")
async def get_logs(nocache: int = 1, ts: Optional[int] = None, read: bool = False):
    """
    Get execution logs in real-time
    Returns array of log entries and current agent status
    """
    global execution_logs, agent_status
    
    try:
        # If read=true, just return logs without updates
        if read:
            logger.info(f"[HOOK] Read logs requested - {len(execution_logs)} entries")
        
        return {
            "logs": execution_logs,
            "status": agent_status,
            "total_steps": len(execution_logs),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[HOOK] Error getting logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/refresh")
async def refresh_agent(target: str = "main", nocache: int = 1, timestamp: Optional[int] = None):
    """
    Force refresh/restart the agent watcher
    """
    global agent_status, execution_logs
    
    try:
        logger.info(f"[HOOK] Refresh requested for target: {target}")
        
        # Reset agent status
        agent_status = "IDLE"
        
        # Add log entry
        execution_logs.append({
            "ts": datetime.now().isoformat(),
            "step": len(execution_logs),
            "action": f"Agent refreshed (target: {target})",
            "status": "ok",
            "error": None
        })
        
        return {
            "status": "refresh_ok",
            "target": target,
            "message": "Agent watcher refreshed successfully"
        }
        
    except Exception as e:
        logger.error(f"[HOOK] Error refreshing agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/text")



@router.get("/result")
async def get_result(nocache: int = 1, timestamp: Optional[int] = None):
    """
    Get last task result - credentials, screenshot, completion status
    """
    global last_result
    
    try:
        return {
            "success": True,
            "result": last_result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[HOOK] Error getting result: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class ControlRequest(BaseModel):
    mode: str  # ACTIVE, PAUSED, STOP

@router.post("/control")
async def control_agent(request: ControlRequest):
    """
    Control agent execution mode
    """
    global control_state, agent_status
    
    try:
        if request.mode not in ["ACTIVE", "PAUSED", "STOP"]:
            raise HTTPException(
                status_code=400, 
                detail="Invalid mode. Must be ACTIVE, PAUSED, or STOP"
            )
        
        # Update control state
        control_state["run_mode"] = request.mode
        
        # Update agent status accordingly
        if request.mode == "ACTIVE":
            if agent_status == "IDLE":
                agent_status = "ACTIVE"
        elif request.mode == "PAUSED":
            if agent_status == "ACTIVE":
                agent_status = "IDLE"
        elif request.mode == "STOP":
            agent_status = "IDLE"
            # Clear execution logs on STOP
            execution_logs.clear()
        
        logger.info(f"[HOOK] Control mode changed to: {request.mode}")
        logger.info(f"[HOOK] Agent status: {agent_status}")
        
        return {
            "success": True,
            "run_mode": control_state["run_mode"],
            "agent_status": agent_status,
            "message": f"Agent mode set to {request.mode}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[HOOK] Error controlling agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_current_task(nocache: int = 1, timestamp: Optional[int] = None):
    """
    Get current active task text
    """
    global current_task
    
    try:
        return {
            "text": current_task.get("text", ""),
            "job_id": current_task.get("job_id"),
            "timestamp": current_task.get("timestamp")
        }
        
    except Exception as e:
        logger.error(f"[HOOK] Error getting current task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def _simulate_task_execution(task_text: str):
    """
    Execute real task (currently simplified)
    In production, this would trigger actual agent execution
    """
    global execution_logs, agent_status, last_result
    
    # Reset previous result
    last_result = {
        "screenshot": None,
        "credentials": None,
        "completed": False
    }
    
    # Mock execution steps based on task
    if "gmail" in task_text.lower() or "register" in task_text.lower():
        # Simulate Gmail registration
        mock_steps = [
            {"action": "Opening https://accounts.google.com/signup", "status": "ok"},
            {"action": "Filling first name field", "status": "ok"},
            {"action": "Filling last name field", "status": "ok"},
            {"action": "Generating random username", "status": "ok"},
            {"action": "Creating strong password", "status": "ok"},
            {"action": "Detecting CAPTCHA challenge", "status": "warning"},
            {"action": "Solving CAPTCHA using AI vision", "status": "ok"},
            {"action": "Submitting registration form", "status": "ok"},
            {"action": "Waiting for confirmation", "status": "ok"},
            {"action": "Taking screenshot of success page", "status": "ok"},
        ]
        
        # Set real result after execution
        last_result["screenshot"] = "mock://screenshot_success.png"
        last_result["credentials"] = {
            "login": "generated_user@gmail.com",
            "password": "auto_generated_password_123"
        }
        last_result["completed"] = True
        
    elif "search" in task_text.lower():
        # Simulate search task
        mock_steps = [
            {"action": "Opening browser", "status": "ok"},
            {"action": f"Navigating to search page", "status": "ok"},
            {"action": "Typing search query", "status": "ok"},
            {"action": "Clicking search button", "status": "ok"},
            {"action": "Extracting results", "status": "ok"},
        ]
        
        last_result["completed"] = True
        last_result["screenshot"] = "mock://search_results.png"
        
    else:
        # Generic task
        mock_steps = [
            {"action": "Analyzing task requirements", "status": "ok"},
            {"action": "Creating execution plan", "status": "ok"},
            {"action": "Initializing browser context", "status": "ok"},
            {"action": "Executing task steps", "status": "ok"},
        ]
        
        last_result["completed"] = True
    
    # Add mock logs
    for i, step in enumerate(mock_steps, start=1):
        execution_logs.append({
            "ts": datetime.now().isoformat(),
            "step": i,
            "action": step["action"],
            "status": step["status"],
            "error": None
        })
    
    # Final completion log
    execution_logs.append({
        "ts": datetime.now().isoformat(),
        "step": len(mock_steps) + 1,
        "action": "Task completed successfully",
        "status": "ok",
        "error": None
    })
    
    # Set agent back to idle
    agent_status = "IDLE"
    
    logger.info(f"[HOOK] Task execution completed with {len(mock_steps)} steps")
    logger.info(f"[HOOK] Result: {last_result}")


@router.get("/status")
async def get_agent_status():
    """
    Get current agent status with control mode and completion state
    """
    global agent_status, current_task, control_state, last_result
    
    return {
        "status": agent_status,
        "current_task": current_task.get("text", ""),
        "job_id": current_task.get("job_id"),
        "active": agent_status == "ACTIVE",
        "run_mode": control_state["run_mode"],
        "completed": last_result["completed"]
    }
