from datetime import datetime

from uuid import UUID

from time import sleep

from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException, UploadFile, BackgroundTasks, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.schemas import ReportCreate
from src.models import Report
from src.logger import logger
from src.services import ImagePreprocessor, BodyPartClassifier, FracturePredictor
from src.database import get_db

import asyncio
import imghdr

class Service:
    def __init__(self):
        self.body_part_classifier = BodyPartClassifier()
        self.fracture_predictor = FracturePredictor()
        self.max_file_size = 10 * 1024 * 1024  # 10MB

    async def update_report_field(self, session: AsyncSession, report_id: UUID, field: str, value):
        """Update a single field in a report record"""
        result = await session.execute(select(Report).where(Report.id == report_id))
        if report := result.scalar_one_or_none():
            setattr(report, field, value)
            await session.commit()
            return True
        return False

    async def predict(self, image_file: UploadFile, background_tasks: BackgroundTasks, db: AsyncSession):
        """Handle image upload and initiate background processing"""
        try:
            # Read and validate file
            file_content = await image_file.read()
            if len(file_content) > self.max_file_size:
                raise HTTPException(status_code=413, detail=f"File exceeds maximum size of {self.max_file_size} bytes")
            
            if not imghdr.what(None, file_content[:512]):
                raise HTTPException(status_code=400, detail="Unsupported or corrupted image format")

            # Create new report record
            new_report = Report(
                filename=image_file.filename,
                format=image_file.content_type,
                received_time=datetime.now(),
                model_time_seconds=0.0,
                body_part="",
                confidence=None,
                prediction="",
                status="In Progress"
            )
            
            db.add(new_report)
            await db.commit()
            await db.refresh(new_report)

            # Start background processing
            background_tasks.add_task(
                self.process_report, 
                new_report.id, 
                file_content,
                image_file.filename,
                image_file.content_type
            )

            return JSONResponse(
                content=jsonable_encoder(new_report),
                status_code=status.HTTP_202_ACCEPTED
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[PREDICT] Internal error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Prediction initialization failed"
            )

    async def process_report(self, report_id: UUID, image_content: bytes, filename: str, content_type: str):
        """Background task to process the image and update report"""
        async for session in get_db():
            try:
                
                await self.update_report_field(session, report_id, 'status', 'Processing')
                await self.update_report_field(session, report_id, 'filename', filename)

                sleep(3)
                image = await ImagePreprocessor.preprocess(image_content)
                
                await self.update_report_field(session, report_id, 'status', 'Classifying Body Part')
                body_part, confidence = await self.retry_async(
                    lambda: self.body_part_classifier.predict(image),
                    max_attempts=3,
                    error_message="Body part classification failed"
                )
                sleep(3)
                await self.update_report_field(session, report_id, 'body_part', body_part)
                await self.update_report_field(session, report_id, 'confidence', confidence)


                await self.update_report_field(session, report_id, 'status', 'Predicting Fracture')
                fracture_label, fracture_conf = await self.retry_async(
                    lambda: self.fracture_predictor.predict(image, body_part),
                    max_attempts=3,
                    error_message="Fracture prediction failed"
                )
                sleep(3)
                await self.update_report_field(session, report_id, 'prediction', fracture_label)
                await self.update_report_field(session, report_id, 'fracture_confidence', fracture_conf)
            
                await self.update_report_field(session, report_id, 'status', 'Completed')
                
                result = await session.execute(select(Report).where(Report.id == report_id))
                if report := result.scalar_one_or_none():
                    duration = (datetime.now() - report.received_time).total_seconds()
                    await self.update_report_field(session, report_id, 'model_time_seconds', duration)


            except Exception as e:
                logger.error(f"[PROCESS] Error processing report {report_id}: {str(e)}")
                await self.update_report_field(session, report_id, 'status', 'Error')
                await self.update_report_field(session, report_id, 'error', "internal server error")

    async def retry_async(self, func, max_attempts=3, delay=1, error_message="Operation failed"):
        """Retry an async operation with exponential backoff"""
        attempt = 0
        last_exception = None

        while attempt < max_attempts:
            try:
                return await func()
            except Exception as e:
                attempt += 1
                last_exception = e
                logger.warning(
                    f"[RETRY] Attempt {attempt}/{max_attempts} failed: {str(last_exception)}"
                )
                if attempt < max_attempts:
                    await asyncio.sleep(delay * attempt)
                    
        raise Exception(f"{error_message}. Final error: {str(last_exception)}")



    async def get_report(self, report_id: UUID, db: AsyncSession):
        """Retrieve a report by ID"""
        try:
            result = await db.scalar(select(Report).where(Report.id == report_id))
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Report not found"
                )
            return ReportCreate.model_validate(result)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[GET_REPORT] Error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve report",
            ) from e