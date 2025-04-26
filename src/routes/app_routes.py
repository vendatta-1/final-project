from fastapi import APIRouter, UploadFile
from fastapi import BackgroundTasks
from fastapi import Depends
from fastapi import Path
from fastapi import HTTPException

from src.services import Service
from src.schemas import ReportCreate
from src.database import get_db

from sqlalchemy.ext.asyncio import AsyncSession

from uuid import UUID


class ModelRoutes:
    
    def __init__(self):
        self.router = APIRouter()
        self.router.add_api_route(
            "/api/", 
            self.receive_image, 
            methods=["POST"], 
            response_model=ReportCreate, 
            status_code=202,
            
        )
        self.router.add_api_route(
            "/api/{report_id}",
            self.get_report,
            methods=["GET"],
            response_model=ReportCreate,
            status_code=201
        )

    async def receive_image(self, image: UploadFile, background_tasks: BackgroundTasks,db:AsyncSession =Depends(get_db)):
        service = Service()
        return await service.predict(image, background_tasks,db)
        
    async def get_report(self,
        report_id: UUID = Path(..., example="6b42a6ea-a41b-47e6-a22d-85811698a237"),
        db: AsyncSession = Depends(get_db)
    ):
        try:
            # Explicit validation
            parsed_uuid = UUID(str(report_id))
        except ValueError as e:
            raise HTTPException(
                status_code=422,
                detail="Invalid UUID format. Must be 32 hexadecimal characters.",
            ) from e

        service = Service()
        return await service.get_report(parsed_uuid, db)