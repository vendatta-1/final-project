from datetime import datetime
from uuid import UUID
from fastapi import UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.encoders import jsonable_encoder
from typing import List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
import asyncio

from src.schemas import ReportResponse, APIResponse, T, ReportCompleteResponse
from src.logger import logger
from src.services.image_validation_service import ImageValidationService, ImagePreprocessor
from src.services.prediction_service import PredictionService
from src.services.report_service import ReportService
from src.database import AsyncSessionLocal
from src.models import Report


class Service:
    def __init__(self):
        self.prediction_service = PredictionService()
        self.report_service = ReportService()
        self.thread_pool = ThreadPoolExecutor(max_workers=4)

    async def predict(self, image_file: UploadFile, background_tasks: BackgroundTasks, db: AsyncSession, body_part: Optional[str] = None):
        try:
            content = await asyncio.get_event_loop().run_in_executor(None, lambda: image_file.file.read())

            if not ImageValidationService.validate_image(content, image_file.filename):
                return self.__handle_failure__(400, None, f"Invalid image format in file {image_file.filename}")

            if not ImageValidationService.validate_image_length(content):
                return self.__handle_failure__(413, None, "File too large")

            report = await self.report_service.create_report(image_file, db)
            await db.commit()

            background_tasks.add_task(self._process_prediction_report, report.id, content, body_part)

            return self.__handle_success__(202, jsonable_encoder(ReportResponse.model_validate(report)))

        except Exception as e:
            await db.rollback()
            logger.error(f"[PREDICT] {e}", exc_info=True)
            return self.__handle_failure__(500, None, "Prediction failed")

    async def _process_prediction_report(self, report_id: UUID, content: bytes, body_part):
        """Process report in background with its own database session"""
        async with AsyncSessionLocal() as db:
            try:
                start_time = datetime.now()

                report = await self.report_service.fetch_report_by_id(report_id, db)
                if not report:
                    logger.error(f"Report {report_id} not found")
                    return

                # Offload CPU-intensive preprocessing
                image = await asyncio.get_event_loop().run_in_executor(
                    self.thread_pool,
                    lambda: ImagePreprocessor.preprocess(content)
                )

                if body_part is None:
                    report = await self.prediction_service.classify_body_part(report, image)
                else:
                    report.body_part = body_part
                    report.confidence = 1.0   
                report = await self.prediction_service.predict_fracture(report, image, start_time, report.body_part)
                await self.report_service.update_report(report, db)
                await db.commit()

            except Exception as e:
                await db.rollback()
                logger.error(f"[PROCESS] {e}", exc_info=True)
                try:
                    if report:
                        report.status = "Error"
                        report.error = str(e)[:200]   
                        await self.report_service.update_report(report, db)
                        await db.commit()
                except Exception as update_error:
                    logger.error(f"[PROCESS UPDATE ERROR] {update_error}")

    async def get_prediction_report(self, report_id: UUID, db: AsyncSession):
        try:
            report = await self.report_service.fetch_report_by_id(report_id, db)
            if not report:
                return self.__handle_failure__(404, None, "Report not found")

            return self.__handle_success__(200, jsonable_encoder(ReportCompleteResponse.model_validate(report)))

        except Exception as e:
            logger.error(f"[GET_REPORT] {e}", exc_info=True)
            return self.__handle_failure__(500, None, "Report fetch failed")
    async def predict_batch(self, images: List[UploadFile], background_tasks: BackgroundTasks, db: AsyncSession, body_parts: Optional[str] = None, use_body_parts: bool = False):
        if use_body_parts:
            return await self._predict_batch_with_body_parts(images, background_tasks, db, body_parts)
        else:
            return await self._predict_batch_without_body_parts(images, background_tasks, db)

    async def _predict_batch_with_body_parts(self, images: List[UploadFile], background_tasks: BackgroundTasks, db: AsyncSession, body_parts: str):
        """Handles batch prediction when body parts are specified"""
        try:
            report_responses: List[dict] = []
            created_reports: List[Tuple[Report, bytes]] = []

            # Handle and validate body parts
            body_part_list = [bp.strip() for bp in body_parts.split(",")]

            if len(body_part_list) == 1:
                body_part_list *= len(images)  # Repeat body part if only one is provided

            elif len(body_part_list) != len(images):
                return self.__handle_failure__(400, None, "Number of body parts must match number of images")

            for image_file in images:
                content = await image_file.read()
                if not ImageValidationService.validate_image(content, image_file.filename):
                    return self.__handle_failure__(400, None, f"Invalid image format in file {image_file.filename}")
                if not ImageValidationService.validate_image_length(content):
                    return self.__handle_failure__(413, None, f"File {image_file.filename} too large")

                report = await self.report_service.create_report(image_file, db)
                created_reports.append((report, content))

            await db.commit()

            # Process each report with specific body part in background
            for idx, (report, content) in enumerate(created_reports):
                body_part = body_part_list[idx] if body_part_list else None
                background_tasks.add_task(self._process_prediction_report, report.id, content, body_part)
                report_responses.append(jsonable_encoder(ReportResponse.model_validate(report)))

            return self.__handle_success__(202, report_responses)

        except Exception as e:
            await db.rollback()
            logger.error(f"[PREDICT_BATCH] {e}", exc_info=True)
            return self.__handle_failure__(500, None, "Batch prediction failed")

    async def _predict_batch_without_body_parts(self, images: List[UploadFile], background_tasks: BackgroundTasks, db: AsyncSession):
        """Handles batch prediction when no body parts are specified"""
        try:
            report_responses: List[dict] = []
            created_reports: List[Tuple[Report, bytes]] = []

            for image_file in images:
                content = await image_file.read()
                if not ImageValidationService.validate_image(content, image_file.filename):
                    return self.__handle_failure__(400, None, f"Invalid image format in file {image_file.filename}")
                if not ImageValidationService.validate_image_length(content):
                    return self.__handle_failure__(413, None, f"File {image_file.filename} too large")

                report = await self.report_service.create_report(image_file, db)
                created_reports.append((report, content))

            await db.commit()

            # Process each report in background without body part
            for report, content in created_reports:
                background_tasks.add_task(self._process_prediction_report, report.id, content, None)
                report_responses.append(jsonable_encoder(ReportResponse.model_validate(report)))

            return self.__handle_success__(202, report_responses)

        except Exception as e:
            await db.rollback()
            logger.error(f"[PREDICT_BATCH] {e}", exc_info=True)
            return self.__handle_failure__(500, None, "Batch prediction failed")

    async def _process_prediction_report(self, report_id: UUID, content: bytes, body_part):
        """Process report in background with its own database session"""
        async with AsyncSessionLocal() as db:
            try:
                start_time = datetime.now()

                report = await self.report_service.fetch_report_by_id(report_id, db)
                if not report:
                    logger.error(f"Report {report_id} not found")
                    return

                # Offload CPU-intensive preprocessing
                image = await asyncio.get_event_loop().run_in_executor(
                    self.thread_pool,
                    lambda: ImagePreprocessor.preprocess(content)
                )

                if body_part is None:
                    report = await self.prediction_service.classify_body_part(report, image)
                else:
                    report.body_part = body_part
                    report.confidence = 1.0
                report = await self.prediction_service.predict_fracture(report, image, start_time, report.body_part)
                await self.report_service.update_report(report, db)
                await db.commit()

            except Exception as e:
                await db.rollback()
                logger.error(f"[PROCESS] {e}", exc_info=True)
                try:
                    if report:
                        report.status = "Error"
                        report.error = str(e)[:200]   
                        await self.report_service.update_report(report, db)
                        await db.commit()
                except Exception as update_error:
                    logger.error(f"[PROCESS UPDATE ERROR] {update_error}")


    def __handle_success__(self, status_code: int, data: Optional[T], error_message=None):
        return JSONResponse(
            status_code=status_code,
            content=APIResponse(
                error_message=error_message,
                data=data,
                is_success=True,
                status_code=str(status_code)
            ).model_dump()
        )

    def __handle_failure__(self, status_code: int, data: Optional[T], error_message):
        return JSONResponse(
            status_code=status_code,
            content=APIResponse(
                error_message=error_message,
                data=None,
                is_success=False,
                status_code=str(status_code)
            ).model_dump()
        )
