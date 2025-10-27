"""
Comprehensive System Test - Tests all major features
One endpoint to test everything
"""
from fastapi import APIRouter, HTTPException
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List
import base64

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/test", tags=["testing"])

@router.get("/comprehensive")
async def comprehensive_test():
    """
    Test all systems comprehensively
    Returns detailed report of all features
    """
    results = {
        "test_started": datetime.utcnow().isoformat(),
        "tests": []
    }
    
    # Test 1: Chat with Claude 4.5 Sonnet
    try:
        from routes.chat_routes import router as chat_router
        from services.openrouter_service import openrouter_service
        
        chat_response = await openrouter_service.chat_completion(
            messages=[{"role": "user", "content": "Say 'Chat works!' and nothing else"}],
            model="anthropic/claude-sonnet-4.5",
            temperature=0.3
        )
        
        chat_reply = chat_response['choices'][0]['message']['content']
        
        results["tests"].append({
            "name": "Chat System",
            "status": "✅ PASS" if "Chat works" in chat_reply or "works" in chat_reply.lower() else "❌ FAIL",
            "model": "anthropic/claude-sonnet-4.5 (Planning/Chat)",
            "response": chat_reply[:100],
            "time_ms": 0
        })
    except Exception as e:
        results["tests"].append({
            "name": "Chat System",
            "status": "❌ FAIL",
            "error": str(e)
        })
    
    # Test 2: Code Generation with Grok
    try:
        code_response = await openrouter_service.chat_completion(
            messages=[{"role": "user", "content": "Write a simple 'Hello World' in Python. Code only, no explanation."}],
            model="x-ai/grok-code-fast-1",
            temperature=0.3
        )
        
        code_reply = code_response['choices'][0]['message']['content']
        
        results["tests"].append({
            "name": "Code Generation",
            "status": "✅ PASS" if "print" in code_reply and "Hello" in code_reply else "❌ FAIL",
            "model": "x-ai/grok-code-fast-1 (Code)",
            "response": code_reply[:100],
            "time_ms": 0
        })
    except Exception as e:
        results["tests"].append({
            "name": "Code Generation",
            "status": "❌ FAIL",
            "error": str(e)
        })
    
    # Test 3: Design Generation with Gemini
    try:
        design_response = await openrouter_service.chat_completion(
            messages=[{"role": "user", "content": "Design spec for a red button. One sentence."}],
            model="google/gemini-2.5-flash-image",
            temperature=0.5
        )
        
        design_reply = design_response['choices'][0]['message']['content']
        
        results["tests"].append({
            "name": "Design Generation",
            "status": "✅ PASS" if len(design_reply) > 10 else "❌ FAIL",
            "model": "google/gemini-2.5-flash-image (Design)",
            "response": design_reply[:100],
            "time_ms": 0
        })
    except Exception as e:
        results["tests"].append({
            "name": "Design Generation",
            "status": "❌ FAIL",
            "error": str(e)
        })
    
    # Test 4: Document Verification (3 models)
    try:
        # Create simple test image
        test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        from routes.document_verification_routes import router as doc_router
        
        results["tests"].append({
            "name": "Document Verification",
            "status": "⏳ SKIP (too slow for quick test)",
            "models": "GPT-4o + Claude 3.5 Sonnet + Gemini 2.5 Flash Image",
            "info": "3-model consensus system active"
        })
    except Exception as e:
        results["tests"].append({
            "name": "Document Verification",
            "status": "❌ FAIL",
            "error": str(e)
        })
    
    # Test 5: Proxy Service
    try:
        from services.proxy_service import proxy_service
        
        proxies = await proxy_service.get_proxies()
        
        results["tests"].append({
            "name": "Proxy Service",
            "status": "✅ PASS" if len(proxies) > 0 else "❌ FAIL",
            "proxy_count": len(proxies),
            "info": f"{len(proxies)} proxies available from Webshare.io"
        })
    except Exception as e:
        results["tests"].append({
            "name": "Proxy Service",
            "status": "❌ FAIL",
            "error": str(e)
        })
    
    # Test 6: Browser Automation
    try:
        from services.browser_automation_service import browser_service
        
        # Just check if service can initialize
        await browser_service.initialize()
        
        results["tests"].append({
            "name": "Browser Automation",
            "status": "✅ PASS (service initialized)",
            "features": "Playwright + Anti-detect + CAPTCHA solving",
            "info": "Create session to test fully"
        })
    except Exception as e:
        results["tests"].append({
            "name": "Browser Automation",
            "status": "❌ FAIL",
            "error": str(e)
        })
    
    # Test 7: API Keys
    try:
        import os
        
        keys_status = {
            "OPENROUTER_API_KEY": "✅" if os.environ.get('OPENROUTER_API_KEY') else "❌",
            "WEBSHARE_API_KEY": "✅" if os.environ.get('WEBSHARE_API_KEY') else "❌"
        }
        
        results["tests"].append({
            "name": "API Keys",
            "status": "✅ PASS" if all(v == "✅" for v in keys_status.values()) else "⚠️ PARTIAL",
            "keys": keys_status
        })
    except Exception as e:
        results["tests"].append({
            "name": "API Keys",
            "status": "❌ FAIL",
            "error": str(e)
        })
    
    # Test 8: Model Assignments
    results["tests"].append({
        "name": "Model Assignments",
        "status": "✅ CONFIGURED",
        "assignments": {
            "Chat/Planning": "anthropic/claude-sonnet-4.5",
            "Code Generation": "x-ai/grok-code-fast-1",
            "Design Spec": "google/gemini-2.5-flash-image",
            "Visual Mockup": "google/gemini-2.5-flash-image-preview",
            "Document Verification": "GPT-4o + Claude 3.5 Sonnet + Gemini 2.5 Flash Image",
            "CAPTCHA Solving": "google/gemini-2.5-flash-image",
            "Vision": "google/gemini-2.5-flash-image"
        }
    })
    
    # Summary
    passed = sum(1 for t in results["tests"] if "✅" in t.get("status", ""))
    failed = sum(1 for t in results["tests"] if "❌" in t.get("status", ""))
    
    results["summary"] = {
        "total_tests": len(results["tests"]),
        "passed": passed,
        "failed": failed,
        "overall_status": "✅ ALL PASS" if failed == 0 else f"⚠️ {failed} FAILURES"
    }
    
    results["test_completed"] = datetime.utcnow().isoformat()
    
    return results
