import asyncio
import imghdr
from datetime import datetime
from uuid import UUID
from fastapi import UploadFile, BackgroundTasks, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models import Report
from src.schemas import ReportCreate
from src.logger import logger
from src.services import ImagePreprocessor, BodyPartClassifier, FracturePredictor


class Service:
    def __init__(self):
        self.body_part_classifier = BodyPartClassifier()
        self.fracture_predictor = FracturePredictor()
        self.max_file_size = 10 * 1024 * 1024  # 10MB

    async def predict(self, image_file: UploadFile, background_tasks: BackgroundTasks, db: AsyncSession):
        try:
            content = await image_file.read()

            if len(content) > self.max_file_size:
                raise HTTPException(status_code=413, detail="File too large")
            if not imghdr.what(None, content[:512]):
                raise HTTPException(status_code=400, detail="Invalid image format")

            report = Report(
                filename=image_file.filename,
                format=image_file.content_type,
                received_time=datetime.now(),
                model_time_seconds=0.0,
                body_part="",
                confidence=None,
                prediction="",
                fracture_confidence=None,
                status="In Progress",
                error=None
            )
            db.add(report)
            await db.commit()
            await db.refresh(report)

            background_tasks.add_task(self.process_report, report.id, content, db)

            return JSONResponse(jsonable_encoder(report), status.HTTP_202_ACCEPTED)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[PREDICT] {e}")
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, "Prediction failed"
            ) from e

    async def process_report(self, report_id: UUID, content: bytes, db: AsyncSession):
        try:
            start_time = datetime.now()
            image = ImagePreprocessor.preprocess(content)

            result = await db.execute(select(Report).where(Report.id == report_id))
            report = result.scalar_one_or_none()
            if not report:
                logger.error(f"[PROCESS] Report {report_id} not found.")
                return

            # Body part classification
            report.status = "Classifying Body Part"
            body_part, confidence = self.body_part_classifier.predict(image)
            report.body_part = body_part
            report.confidence = confidence

            # Fracture prediction
            report.status = "Predicting Fracture"
            label, frac_conf = self.fracture_predictor.predict(image, body_part)
            report.prediction = label
            report.fracture_confidence = frac_conf

            # Final update
            report.status = "Completed"
            report.model_time_seconds = (datetime.now() - start_time).total_seconds()
            await db.commit()

        except Exception as e:
            logger.error(f"[PROCESS] {e}")
            # fallback update in case of error
            result = await db.execute(select(Report).where(Report.id == report_id))
            if report := result.scalar_one_or_none():
                report.status = "Error"
                report.error = "Internal server error"
                await db.commit()

    async def get_report(self, report_id: UUID, db: AsyncSession):
        try:
            report = await db.scalar(select(Report).where(Report.id == report_id))
            if not report:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")
            return ReportCreate.model_validate(report)
        except Exception as e:
            logger.error(f"[GET_REPORT] {e}")
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, "Report fetch failed"
            ) from e
