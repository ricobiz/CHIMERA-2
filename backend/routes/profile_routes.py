from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from services.profile_service import profile_service

router = APIRouter(prefix="/api/profile", tags=["profiles"])
logger = logging.getLogger(__name__)

class CreateProfileRequest(BaseModel):
    region: Optional[str] = None
    proxy_tier: Optional[str] = None
    warmup: bool = True

class UseProfileRequest(BaseModel):
    profile_id: str

class CheckProfileRequest(BaseModel):
    profile_id: str

@router.post("/create")
async def create_profile(req: CreateProfileRequest):
    try:
        result = await profile_service.create_profile(region=req.region, proxy_tier=req.proxy_tier, warmup=req.warmup)
        return result
    except Exception as e:
        logger.error(f"Profile create error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/use")
async def use_profile(req: UseProfileRequest):
    try:
        result = await profile_service.use_profile(req.profile_id)
        return result
    except Exception as e:
        logger.error(f"Profile use error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check")
async def check_profile(req: CheckProfileRequest):
    try:
        result = await profile_service.check_profile(req.profile_id)
        return result
    except Exception as e:
        logger.error(f"Profile check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{profile_id}/status")
async def status_profile(profile_id: str):
    try:
        result = profile_service.status(profile_id)
        return result
    except Exception as e:
        logger.error(f"Profile status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
