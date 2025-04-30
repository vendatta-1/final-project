from fastapi import APIRouter, UploadFile, BackgroundTasks, Depends, Path, HTTPException, File
from typing import List
from uuid import UUID

from src.services import Service
from src.schemas import ReportCreate, ReportResponse, APIResponse
from src.database import get_db
from src.models import Report
from sqlalchemy.ext.asyncio import AsyncSession

class ModelRoutes:
    def __init__(self):
        self.router = APIRouter()
        self.service = Service()
        self.router.add_api_route(
            "/ai/", 
            self.predict_single,
            methods=["POST"], 
            response_model=APIResponse, 
            status_code=202
        )
        self.router.add_api_route(
            "/ai/{report_id}",
            self.get_report,
            methods=["GET"],
            response_model=APIResponse,
            status_code=201
        )
        self.router.add_api_route(
            '/ai/batch',
            self.predict_batch,
            methods=['POST'],
            response_model=APIResponse,
            status_code=200
        )


    async def predict_single(self, image: UploadFile, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
        return await self.service.predict(image, background_tasks, db)
        
    async def get_report(self, report_id: UUID, db: AsyncSession = Depends(get_db)):
        try: 
            parsed_uuid = UUID(str(report_id))
        except ValueError as e:
            raise HTTPException(
                status_code=422,
                detail="Invalid UUID format. Must be 32 hexadecimal characters.",
            ) from e

        return await self.service.get_report(parsed_uuid, db)
    
    async def predict_batch(self, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db), images: List[UploadFile] = File(...)):
        if images:
            return await self.service.predict_batch(images, background_tasks, db)
        else:
            raise HTTPException(status_code=400, detail="No images provided")
    

    
    def __handle_success__(self, status_code: int, data: ReportResponse):
        return APIResponse(
            error_message=None,
            data=data,
            is_success=True,
            status_code=str(status_code)   
        ).model_dump()

    def __handle_failure__(self, status_code: int, error_message: str):
        return APIResponse(
            error_message=error_message,
            data=None,
            is_success=False,
            status_code=str(status_code)   
        ).model_dump()
