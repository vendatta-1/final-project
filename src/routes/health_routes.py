from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.services.health_service import SystemHealthService
from src.schemas.health_response import HealthStatus, ModelStatus
from src.schemas.services_schema import APIResponse
from src.limiters import limiter   
from typing import List
from starlette.requests import Request

class HealthRoutes:
    def __init__(self):
        self.router = APIRouter(
            prefix="/health",
            tags=["System Health"]
        )
        self._register_routes()

    def _register_routes(self):
        self.router.add_api_route(
            "/database",
            self.check_db_health,
            methods=["GET"],
            response_model=APIResponse[HealthStatus],
            summary="Check database health"
        )
        self.router.add_api_route(
            "/models",
            self.check_models_health,
            methods=["GET"],
            response_model=APIResponse[ModelStatus],
            summary="Check model files health"
        )
        self.router.add_api_route(
            "/full",
            self.full_health_check,
            methods=["GET"],
            response_model=APIResponse[List[HealthStatus]],
            summary="Complete system health check"
        )

    # @limiter.limit('2/minute')
    async def check_db_health(self, db: AsyncSession = Depends(get_db)):
        return await SystemHealthService.check_db_health(db)

    async def check_models_health(self):
        return await SystemHealthService.check_models_health()

    async def full_health_check(self, db: AsyncSession = Depends(get_db)):
        return await SystemHealthService.full_health_check(db)
