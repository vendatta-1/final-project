from src.schemas.model_sta import ModelStatisticsBase
from src.database import get_db
from src.schemas.services_schema import APIResponse  # Generic APIResponse[T]

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, status
from sqlalchemy import text

from typing import List


class StatisticsService:

    MODELS = ['ELBOW', 'FINGER', 'FOREARM', 'HAND', 'HUMERUS', 'SHOULDER', 'WRIST']

    @staticmethod
    async def get_all_models_statistics(
        db: AsyncSession = Depends(get_db)
    ) -> APIResponse[List[ModelStatisticsBase]]:
        """Get statistics for all models"""
        try:
            result = await db.execute(text("SELECT * FROM get_all_models_statistics();"))
            rows = result.mappings().all()
            data = [ModelStatisticsBase(**row) for row in rows] if rows else []

            return APIResponse[List[ModelStatisticsBase]](
                is_success=True,
                status_code=str(status.HTTP_200_OK),
                data=data
            )
        except Exception as e:
            return APIResponse[List[ModelStatisticsBase]](
                is_success=False,
                error_message=f"Failed to fetch model statistics: {str(e)}",
                status_code=str(status.HTTP_503_SERVICE_UNAVAILABLE),
                data=[]  # or None
            )

    @staticmethod
    async def get_model_statistics(
        model_name: str,
        db: AsyncSession = Depends(get_db)
    ) -> APIResponse[ModelStatisticsBase]:
        """Get statistics for a specific model"""
        if model_name.upper() not in StatisticsService.MODELS:
            return APIResponse[ModelStatisticsBase](
                is_success=False,
                error_message=f"Invalid model name. Available models: {', '.join(StatisticsService.MODELS)}",
                status_code=str(status.HTTP_400_BAD_REQUEST),
                data=None
            )

        try:
            result = await db.execute(
                text("SELECT * FROM get_model_statistics(:name);"),
                {'name': model_name.upper()}
            )
            if row := result.mappings().first():
                return APIResponse[ModelStatisticsBase](
                    is_success=True,
                    status_code=str(status.HTTP_200_OK),
                    data=ModelStatisticsBase(**row)
                )
            else:
                return APIResponse[ModelStatisticsBase](
                    is_success=False,
                    error_message=f"No statistics found for model: {model_name}",
                    status_code=str(status.HTTP_404_NOT_FOUND),
                    data=None
                )

        except Exception as e:
            return APIResponse[ModelStatisticsBase](
                is_success=False,
                error_message=f"Failed to fetch statistics for model {model_name}: {str(e)}",
                status_code=str(status.HTTP_503_SERVICE_UNAVAILABLE),
                data=None
            )
