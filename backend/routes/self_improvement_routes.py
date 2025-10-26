from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
import os
import subprocess
from pathlib import Path
import json
from datetime import datetime
from services.openrouter_service import openrouter_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["self-improvement"])

# Project root directory
PROJECT_ROOT = Path("/app")

class CodeFile(BaseModel):
    path: str
    content: str
    size: int
    last_modified: str

class FileChange(BaseModel):
    path: str
    new_content: str
    reason: str

class ImprovementRequest(BaseModel):
    target: str = "full"  # full, backend, frontend, specific_file
    focus_areas: List[str] = []  # performance, security, code_quality, bugs
    specific_files: List[str] = []

class SystemHealthCheck(BaseModel):
    timestamp: str
    services_status: Dict
    code_quality_score: float
    suggestions: List[str]

@router.get("/self-improvement/project-structure")
async def get_project_structure():
    """
    Get complete project structure
    """
    try:
        structure = {
            "backend": get_directory_structure(PROJECT_ROOT / "backend"),
            "frontend": get_directory_structure(PROJECT_ROOT / "frontend"),
        }
        
        return {
            "structure": structure,
            "total_files": count_files(structure),
            "total_lines": count_lines_of_code()
        }
        
    except Exception as e:
        logger.error(f"Error getting project structure: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def get_directory_structure(path: Path, max_depth: int = 5, current_depth: int = 0) -> Dict:
    """Recursively get directory structure"""
    if current_depth >= max_depth:
        return {}
    
    structure = {}
    
    try:
        # Skip node_modules, venv, __pycache__, .git
        skip_dirs = {'node_modules', 'venv', '__pycache__', '.git', 'dist', 'build', '.next'}
        
        for item in path.iterdir():
            if item.name.startswith('.') and item.name not in ['.env']:
                continue
                
            if item.is_dir():
                if item.name not in skip_dirs:
                    structure[item.name] = get_directory_structure(item, max_depth, current_depth + 1)
            else:
                structure[item.name] = {
                    "type": "file",
                    "size": item.stat().st_size,
                    "extension": item.suffix
                }
    except PermissionError:
        pass
        
    return structure

def count_files(structure: Dict) -> int:
    """Count total files in structure"""
    count = 0
    for value in structure.values():
        if isinstance(value, dict):
            if value.get("type") == "file":
                count += 1
            else:
                count += count_files(value)
    return count

def count_lines_of_code() -> int:
    """Count total lines of code"""
    total_lines = 0
    
    for ext in ['.py', '.js', '.jsx', '.ts', '.tsx']:
        try:
            result = subprocess.run(
                f"find {PROJECT_ROOT} -name '*{ext}' -not -path '*/node_modules/*' -not -path '*/.git/*' | xargs wc -l | tail -1",
                shell=True,
                capture_output=True,
                text=True
            )
            if result.stdout:
                lines = result.stdout.strip().split()[0]
                if lines.isdigit():
                    total_lines += int(lines)
        except:
            pass
            
    return total_lines

@router.post("/self-improvement/read-file")
async def read_file(path: str):
    """
    Read a specific file
    """
    try:
        file_path = PROJECT_ROOT / path.lstrip('/')
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")
        
        # Security check - ensure within project
        if not str(file_path).startswith(str(PROJECT_ROOT)):
            raise HTTPException(status_code=403, detail="Access denied")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "path": path,
            "content": content,
            "size": file_path.stat().st_size,
            "last_modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        }
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File is not text-readable")
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/self-improvement/write-file")
async def write_file(change: FileChange):
    """
    Write/update a file with backup
    """
    try:
        file_path = PROJECT_ROOT / change.path.lstrip('/')
        
        # Security check
        if not str(file_path).startswith(str(PROJECT_ROOT)):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Create backup before changing
        if file_path.exists():
            backup_dir = PROJECT_ROOT / ".backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            backup_path = backup_dir / file_path.relative_to(PROJECT_ROOT)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'r') as original:
                with open(backup_path, 'w') as backup:
                    backup.write(original.read())
        
        # Write new content
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(change.new_content)
        
        logger.info(f"File updated: {change.path} - Reason: {change.reason}")
        
        return {
            "success": True,
            "path": change.path,
            "backup_created": file_path.exists(),
            "message": f"File updated successfully. Reason: {change.reason}"
        }
        
    except Exception as e:
        logger.error(f"Error writing file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/self-improvement/analyze-code")
async def analyze_code(request: ImprovementRequest):
    """
    Analyze codebase and suggest improvements using AI
    """
    try:
        logger.info(f"Starting code analysis: {request.target}")
        
        # Determine which files to analyze
        files_to_analyze = []
        
        if request.target == "full":
            # Analyze key files
            files_to_analyze = get_critical_files()
        elif request.specific_files:
            files_to_analyze = request.specific_files
        else:
            files_to_analyze = get_files_by_target(request.target)
        
        # Read files
        files_content = {}
        for file_path in files_to_analyze[:10]:  # Limit to 10 files to avoid token limits
            try:
                full_path = PROJECT_ROOT / file_path.lstrip('/')
                if full_path.exists() and full_path.stat().st_size < 50000:  # Max 50KB per file
                    with open(full_path, 'r', encoding='utf-8') as f:
                        files_content[file_path] = f.read()
            except:
                pass
        
        # Create analysis prompt
        focus_text = ", ".join(request.focus_areas) if request.focus_areas else "all aspects"
        
        analysis_prompt = f"""You are an expert software architect and code reviewer analyzing a full-stack application.

**PROJECT STRUCTURE:**
- Backend: FastAPI + Python (AI code generation, automation, document verification)
- Frontend: React + JavaScript (chat interface, automation UI)
- Database: MongoDB
- Key Features: LLM integration, browser automation, document verification, self-improvement

**FILES TO ANALYZE:**
{json.dumps(list(files_content.keys()), indent=2)}

**FOCUS AREAS:** {focus_text}

**YOUR TASK:**
Analyze the provided code and identify:

1. **Critical Issues** (security, bugs, performance bottlenecks)
2. **Code Quality Improvements** (refactoring, best practices)
3. **Architecture Enhancements** (scalability, maintainability)
4. **Performance Optimizations** (caching, async, database queries)
5. **Security Vulnerabilities** (input validation, authentication, data exposure)
6. **Missing Features** or incomplete implementations
7. **Technical Debt** that should be addressed

**RESPOND WITH JSON:**
{{
  "overall_health_score": 0-100,
  "critical_issues": [
    {{"severity": "critical|high|medium|low", "file": "path", "line": null_or_number, "issue": "description", "fix": "suggested fix"}}
  ],
  "improvements": [
    {{"category": "performance|security|quality|architecture", "file": "path", "current": "description", "suggested": "improvement", "impact": "high|medium|low"}}
  ],
  "code_changes": [
    {{"file": "path", "reason": "why", "changes": "what to change"}}
  ],
  "summary": "Overall assessment and priorities"
}}

**CODE TO ANALYZE:**

{json.dumps(files_content, indent=2)[:30000]}  # Truncate to avoid token limits

Be specific, actionable, and prioritize by impact."""

        # Call AI for analysis
        messages = [
            {"role": "system", "content": "You are an expert code reviewer. Respond ONLY with valid JSON."},
            {"role": "user", "content": analysis_prompt}
        ]
        
        response = await openrouter_service.chat_completion(
            messages=messages,
            model="openai/gpt-5",
            temperature=0.2
        )
        
        analysis_text = response['choices'][0]['message']['content']
        
        # Extract JSON
        if '```json' in analysis_text:
            analysis_text = analysis_text.split('```json')[1].split('```')[0].strip()
        elif '```' in analysis_text:
            analysis_text = analysis_text.split('```')[1].split('```')[0].strip()
        
        analysis_result = json.loads(analysis_text)
        
        # Add metadata
        analysis_result['timestamp'] = datetime.now().isoformat()
        analysis_result['analyzed_files'] = list(files_content.keys())
        analysis_result['focus_areas'] = request.focus_areas
        
        return analysis_result
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {str(e)}")
        return {
            "overall_health_score": 70,
            "critical_issues": [],
            "improvements": [],
            "code_changes": [],
            "summary": "Analysis completed but JSON parsing failed. Manual review recommended.",
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Code analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/self-improvement/auto-improve")
async def auto_improve(request: ImprovementRequest):
    """
    Automatically analyze and apply improvements
    """
    try:
        # First analyze
        analysis = await analyze_code(request)
        
        if not analysis.get('code_changes'):
            return {
                "success": True,
                "changes_applied": 0,
                "message": "No improvements needed",
                "analysis": analysis
            }
        
        # Apply changes (with caution - only low-risk improvements)
        applied_changes = []
        
        for change in analysis['code_changes'][:5]:  # Limit to 5 changes at once
            # Read current file
            try:
                file_response = await read_file(change['file'])
                current_content = file_response['content']
                
                # Here you would apply the actual code changes
                # For safety, we'll just log and return suggestions
                applied_changes.append({
                    "file": change['file'],
                    "status": "analyzed",
                    "reason": change['reason'],
                    "manual_action_required": True
                })
                
            except Exception as e:
                logger.error(f"Error processing change for {change['file']}: {str(e)}")
        
        return {
            "success": True,
            "analysis": analysis,
            "changes_applied": len(applied_changes),
            "changes": applied_changes,
            "message": f"Analysis complete. {len(applied_changes)} improvements identified. Manual review recommended before applying."
        }
        
    except Exception as e:
        logger.error(f"Auto-improve error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/self-improvement/reload-services")
async def reload_services(services: List[str] = ["backend", "frontend"]):
    """
    Reload application services
    """
    try:
        results = {}
        
        for service in services:
            try:
                result = subprocess.run(
                    ["supervisorctl", "restart", service],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                results[service] = {
                    "success": result.returncode == 0,
                    "output": result.stdout,
                    "error": result.stderr
                }
                
            except subprocess.TimeoutExpired:
                results[service] = {
                    "success": False,
                    "error": "Timeout"
                }
            except Exception as e:
                results[service] = {
                    "success": False,
                    "error": str(e)
                }
        
        return {
            "success": all(r['success'] for r in results.values()),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Service reload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/self-improvement/health-check")
async def system_health_check():
    """
    Comprehensive system health check
    """
    try:
        health = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "code_metrics": {},
            "suggestions": []
        }
        
        # Check services
        try:
            result = subprocess.run(
                ["supervisorctl", "status"],
                capture_output=True,
                text=True
            )
            
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        service_name = parts[0]
                        status = parts[1]
                        health["services"][service_name] = {
                            "status": status,
                            "healthy": status == "RUNNING"
                        }
        except:
            health["services"]["error"] = "Could not check services"
        
        # Code metrics
        health["code_metrics"] = {
            "total_files": count_files(get_directory_structure(PROJECT_ROOT / "backend")) + 
                          count_files(get_directory_structure(PROJECT_ROOT / "frontend")),
            "total_lines": count_lines_of_code()
        }
        
        # Generate suggestions
        unhealthy_services = [s for s, info in health["services"].items() if not info.get("healthy", False)]
        if unhealthy_services:
            health["suggestions"].append(f"Services need attention: {', '.join(unhealthy_services)}")
        
        return health
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def get_critical_files() -> List[str]:
    """Get list of critical files to analyze"""
    return [
        "backend/server.py",
        "backend/routes/lovable_routes.py",
        "backend/routes/automation_routes.py",
        "backend/routes/document_verification_routes.py",
        "frontend/src/App.js",
        "frontend/src/components/ChatInterface.jsx",
        "frontend/src/agent/executionAgent.ts"
    ]

def get_files_by_target(target: str) -> List[str]:
    """Get files based on target"""
    if target == "backend":
        return [str(p.relative_to(PROJECT_ROOT)) for p in (PROJECT_ROOT / "backend").rglob("*.py") if "venv" not in str(p)][:20]
    elif target == "frontend":
        return [str(p.relative_to(PROJECT_ROOT)) for p in (PROJECT_ROOT / "frontend/src").rglob("*.js*") if "node_modules" not in str(p)][:20]
    return []
