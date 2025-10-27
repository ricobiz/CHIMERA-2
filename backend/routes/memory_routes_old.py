# ============================================================
# AI MEMORY ROUTES - DISABLED FOR MVP DEPLOYMENT
# ============================================================
# Semantic RAG memory (embeddings, torch, ChromaDB) removed
# Will be re-implemented later using external embedding API
# and MongoDB/Postgres storage instead of local ChromaDB
# ============================================================

from fastapi import APIRouter
import logging

router = APIRouter(prefix="/api/memory", tags=["memory"])
logger = logging.getLogger(__name__)

# All memory endpoints temporarily disabled
# TODO: Re-implement with external embedding service (OpenAI/Cohere)
# and MongoDB vector storage

"""
# Original imports (disabled):
# from services.ai_memory_service import memory_service
# from pydantic import BaseModel
# from typing import List, Dict, Any, Optional

# Endpoints that were disabled:
# - POST /api/memory/remember/fact
# - POST /api/memory/remember/automation
# - POST /api/memory/remember/conversation
# - POST /api/memory/recall
# - GET /api/memory/stats
# - DELETE /api/memory/clear
"""

@router.get("/health")
async def memory_health():
    """Health check endpoint - memory system disabled"""
    return {
        "status": "disabled",
        "message": "Semantic memory temporarily disabled for MVP. Will be re-implemented with external embedding API."
    }
