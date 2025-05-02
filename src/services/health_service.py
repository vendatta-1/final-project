from src.database import get_db

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.predictors import MODEL_DIR
from src.schemas.health_response import HealthStatus, ModelStatus
from src.schemas.services_schema import APIResponse  # Ensure this is the generic response
from src.services.statistics_service import StatisticsService

import glob
import os

from fastapi import Depends, status

from typing import List

class SystemHealthService:

    @staticmethod
    async def check_db_health(db: AsyncSession = Depends(get_db)) -> APIResponse[HealthStatus]:
        """Check database connectivity"""
        try:
            await db.execute(text('SELECT 1;'))
            return APIResponse[HealthStatus](
                is_success=True,
                status_code=str(status.HTTP_200_OK),
                data=HealthStatus(
                    service="database",
                    status="healthy",
                    details="Connection successful"
                )
            )
        except Exception as e:
            return APIResponse[HealthStatus](
                is_success=False,
                error_message=str(e),
                status_code=str(status.HTTP_503_SERVICE_UNAVAILABLE),
                data=HealthStatus(
                    service="database",
                    status="unhealthy",
                    details=str(e)
                )
            )

    @staticmethod
    async def check_models_health() -> APIResponse[ModelStatus]:
        """Check if all required models are present"""
        try:
            pattern = os.path.join(MODEL_DIR, '**', '*.h5')
            model_files = glob.glob(pattern, recursive=True)
            expected_count = 8  # Update this with your actual expected count

            if len(model_files) == expected_count:
                return APIResponse[ModelStatus](
                    is_success=True,
                    status_code=str(status.HTTP_200_OK),
                    data=ModelStatus(
                        status="healthy",
                        missing_models=[],
                        details=f"All {expected_count} models found"
                    )
                )

            found_models = [os.path.splitext(os.path.basename(f))[0] for f in model_files]
            missing = [m for m in StatisticsService.MODELS if m not in found_models]

            return APIResponse[ModelStatus](
                is_success=False,
                status_code=str(status.HTTP_206_PARTIAL_CONTENT),
                data=ModelStatus(
                    status="degraded",
                    missing_models=missing,
                    details=f"Found {len(model_files)}/{expected_count} models"
                )
            )

        except Exception as e:
            return APIResponse[ModelStatus](
                is_success=False,
                error_message=str(e),
                status_code=str(status.HTTP_503_SERVICE_UNAVAILABLE),
                data=ModelStatus(
                    status="unhealthy",
                    missing_models=StatisticsService.MODELS,
                    details=str(e)
                )
            )
    @staticmethod
    async def full_health_check(db: AsyncSession) -> APIResponse[List[HealthStatus]]:
        """Aggregate health status of all system components"""
        db_health: APIResponse[HealthStatus] = await SystemHealthService.check_db_health(db)
        models_health: APIResponse[ModelStatus] = await SystemHealthService.check_models_health()

        overall_success = db_health.is_success and models_health.is_success

        # Convert ModelStatus to HealthStatus for unified response
        model_health_status = HealthStatus(
            service="model-check",
            status=models_health.data.status,
            details=models_health.data.details
        )

        return APIResponse[List[HealthStatus]](
            is_success=overall_success,
            status_code=str(status.HTTP_200_OK if overall_success else status.HTTP_206_PARTIAL_CONTENT),
            data=[db_health.data, model_health_status],
            error_message=db_health.error_message or models_health.error_message
        )