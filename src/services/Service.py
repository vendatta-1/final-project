import imghdr
from datetime import datetime
from uuid import UUID

from fastapi import UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.encoders import jsonable_encoder  # Import jsonable_encoder

from typing import List, Optional

from src.models import Report
from src.schemas import ReportCreate, ReportResponse, APIResponse, T
from src.logger import logger
from src.services import ImagePreprocessor, BodyPartClassifier, FracturePredictor


class Service:
    def __init__(self):
        self.body_part_classifier = BodyPartClassifier()
        self.fracture_predictor = FracturePredictor()
        self.max_file_size = 10 * 1024 * 1024

    async def predict(self, image_file: UploadFile, background_tasks: BackgroundTasks, db: AsyncSession):
        try:
            content = await image_file.read()

            if not self._validate_image(content, image_file.filename):
                return self.__handle_failure__(400, None, f"Invalid image format in file {image_file.filename}")

            if len(content) > self.max_file_size:
                return self.__handle_failure__(413, None, "File too large")

            report = await self._create_report(image_file, db)

            background_tasks.add_task(self._process_report, report.id, content, db)

            report_response = jsonable_encoder(ReportResponse.model_validate(report))
            return self.__handle_success__(202, report_response)

        except Exception as e:
            logger.error(f"[PREDICT] {e}")
            return self.__handle_failure__(500, None, "Prediction failed")

    async def _create_report(self, image_file: UploadFile, db: AsyncSession):
        report = Report(
            filename=image_file.filename,
            format=image_file.content_type,
            received_time=datetime.now(),
            model_time_seconds=0.0,
            body_part="",
            confidence=0.0,
            prediction="",
            fracture_confidence=0.0,
            status="In Progress",
            error=''
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)
        return report

    async def _process_report(self, report_id: UUID, content: bytes, db: AsyncSession):
        try:
            start_time = datetime.now()
            image = ImagePreprocessor.preprocess(content)

            report = await self._fetch_report_by_id(report_id, db)
            if not report:
                return

            await self._classify_body_part(report, image, db)
            await self._predict_fracture(report, image, db, start_time)

        except Exception as e:
            logger.error(f"[PROCESS] {e}")
            report = await self._fetch_report_by_id(report_id, db)
            if report:
                report.status = "Error"
                report.error = "Internal server error"
                await db.commit()

    async def _fetch_report_by_id(self, report_id: UUID, db: AsyncSession):
        result = await db.execute(select(Report).where(Report.id == report_id))
        return result.scalar_one_or_none()

    async def _classify_body_part(self, report: Report, image: bytes, db: AsyncSession):
        report.status = "Classifying"
        body_part, confidence = self.body_part_classifier.predict(image)
        report.body_part = body_part
        report.confidence = confidence
        await db.commit()

    async def _predict_fracture(self, report: Report, image: bytes, db: AsyncSession, start_time: datetime):
        report.status = "Predicting"
        label, frac_conf = self.fracture_predictor.predict(image, report.body_part)
        report.prediction = label
        report.fracture_confidence = frac_conf

        report.status = "Completed"
        report.model_time_seconds = (datetime.now() - start_time).total_seconds()
        await db.commit()

    async def get_report(self, report_id: UUID, db: AsyncSession):
        try:
            report = await db.scalar(select(Report).where(Report.id == report_id))
            if not report:
                return self.__handle_failure__(404, None, "Report not found")


            report_response = jsonable_encoder(ReportCreate.model_validate(report))
            return self.__handle_success__(200, report_response)

        except Exception as e:
            logger.error(f"[GET_REPORT] {e}")
            return self.__handle_failure__(500, None, "Report fetch failed")

    async def predict_batch(self, images: List[UploadFile], background_tasks: BackgroundTasks, db: AsyncSession):
        report_responses = []

        for image_file in images:
            try:
                content = await image_file.read()

                if not self._validate_image(content, image_file.filename):
                    return self.__handle_failure__(400, None, f"Invalid image format in file {image_file.filename}")

                if len(content) > self.max_file_size:
                    return self.__handle_failure__(413, None, f"File {image_file.filename} too large")

                report = await self._create_report(image_file, db)

                background_tasks.add_task(self._process_report, report.id, content, db)

                # report_dict = jsonable_encoder(report)
                report_response =jsonable_encoder( ReportResponse.model_validate(report))
                report_responses.append(report_response)

            except Exception as e:
                logger.error(f"[PREDICT_BATCH] Error processing {image_file.filename}: {e}")
                return self.__handle_failure__(500, None, f"Batch prediction failed for file {image_file.filename}")

        return self.__handle_success__(202, report_responses)

    def _validate_image(self, content: bytes, filename: str):
        return bool(imghdr.what(None, content[:512]))

    def __handle_success__(self, status_code: int, data: Optional[T], error_message=None):
        return JSONResponse(
            status_code=status_code,
            content=APIResponse(
                error_message=error_message,
                data=data,
                is_success=True,
                status_code=str(status_code)
            ).dict()
        )

    def __handle_failure__(self, status_code: int, data: Optional[T], error_message):
        return JSONResponse(
            status_code=status_code,
            content=APIResponse(
                error_message=error_message,
                data=None,
                is_success=False,
                status_code=str(status_code)
            ).dict()
        )
