from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.services.health_service import SystemHealthService
from src.schemas.health_response import HealthStatus, ModelStatus
from src.schemas.services_schema import APIResponse
from typing import List
from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

def create_health_router():
    router = APIRouter(
        prefix="/health",
        tags=["System Health"]
    )

    @router.get("/database", response_model=APIResponse[HealthStatus], summary="Check database health")
    @limiter.limit("2/minute")
    async def check_db_health(request: Request, db: AsyncSession = Depends(get_db)):
        return await SystemHealthService.check_db_health(db)

    @router.get("/models", response_model=APIResponse[ModelStatus], summary="Check model files health")
    @limiter.limit("2/minute")
    async def check_models_health(request: Request):
        return await SystemHealthService.check_models_health()

    @router.get("/full", response_model=APIResponse[List[HealthStatus]], summary="Complete system health check")
    @limiter.limit("1/minute")
    async def full_health_check(request: Request, db: AsyncSession = Depends(get_db)):
        return await SystemHealthService.full_health_check(db)

    return router