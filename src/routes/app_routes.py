from fastapi import APIRouter, UploadFile
from fastapi import BackgroundTasks
from fastapi import Depends
from fastapi import Path
from fastapi import HTTPException

from src.services import Service
from src.schemas import ReportCreate
from src.database import get_db
from src.models import Report

from sqlalchemy.ext.asyncio import AsyncSession

from uuid import UUID

from typing import List

class ModelRoutes:
    
    def __init__(self):
        self.router = APIRouter()
        self.service = Service()
        self.router.add_api_route(
            "/ai/", 
            self.get_image,
            methods=["POST"], 
            response_model=ReportCreate, 
            status_code=202,
            
        )
        self.router.add_api_route(
            "/ai/{report_id}",
            self.get_report,
            methods=["GET"],
            response_model=ReportCreate,
            status_code=201
        )

    async def get_image(self, image: UploadFile, background_tasks: BackgroundTasks,db:AsyncSession =Depends(get_db)):
        
        return await self.service.predict(image, background_tasks,db)
        
    async def get_report(self,
        report_id: UUID,
        db: AsyncSession = Depends(get_db)
    ):
        try: 
            
            parsed_uuid = UUID(str(report_id))
        except ValueError as e:
            raise HTTPException(
                status_code=422,
                detail="Invalid UUID format. Must be 32 hexadecimal characters.",
            ) from e

        return await self.service.get_report(parsed_uuid, db)
    
    async def get_images(self,images: List[UploadFile],background_task: BackgroundTasks, db:AsyncSession=Depends(get_db) ):
        if len(images) > 0:
            for image in images:
                await self.service.predict(image,background_task,db)
            