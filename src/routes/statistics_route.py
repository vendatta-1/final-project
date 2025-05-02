from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.statistics_service import StatisticsService
from src.database import get_db
from src.schemas.services_schema import APIResponse
from typing import List
from src.schemas.model_sta import ModelStatisticsBase


class StatisticsRoutes:
    def __init__(self):
        self.router = APIRouter(
            prefix="/statistics",
            tags=["Model Statistics"]
        )
        self._register_routes()

    def _register_routes(self):
        self.router.add_api_route(
            "/models",
            self.get_all_models_stats,
            methods=["GET"],
            response_model=APIResponse[List[ModelStatisticsBase]],   
            summary="Get statistics for all models"
        )
        self.router.add_api_route(
            "/models/{model_name}",
            self.get_model_stats,
            methods=["GET"],
            response_model=APIResponse[ModelStatisticsBase],   
            summary="Get statistics for a specific model"
        )

    async def get_all_models_stats(self, db: AsyncSession = Depends(get_db)):
        return await StatisticsService.get_all_models_statistics(db)

    async def get_model_stats(self, model_name: str, db: AsyncSession = Depends(get_db)):
        return await StatisticsService.get_model_statistics(model_name, db)
