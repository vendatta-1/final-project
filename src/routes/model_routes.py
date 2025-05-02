from fastapi import (
    APIRouter,
    UploadFile,
    BackgroundTasks,
    Depends,
    HTTPException,
    File,
    Query,
    Path,
)
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.services import Service
from src.schemas import APIResponse
from src.database import get_db


class MedicalImageAnalysisRoutes:
    def __init__(self):
        self.router = APIRouter(
            prefix="/medical-image-analysis",
            tags=["Medical Image Analysis"]
        )
        self.service = Service()
        self._register_routes()

    def _register_routes(self):
        # Define the API routes
        self.router.add_api_route(
            "/single", 
            self.analyze_image,
            methods=["POST"], 
            response_model=APIResponse, 
            status_code=202,
            summary="Analyze a single image (auto-detect body part)"
        )
        
        self.router.add_api_route(
            "/single/with-body-part", 
            self.analyze_image_with_body_part,
            methods=["POST"], 
            response_model=APIResponse, 
            status_code=202,
            summary="Analyze a single image with specified body part"
        )
        
        self.router.add_api_route(
            "/batch",
            self.analyze_batch,
            methods=['POST'],
            response_model=APIResponse,
            status_code=202,
            summary="Analyze a batch of images (auto-detect body parts)"
        )
        
        self.router.add_api_route(
            "/batch/with-body-parts",
            self.analyze_batch_with_body_parts,
            methods=['POST'],
            response_model=APIResponse,
            status_code=202,
            summary="Analyze a batch with specified body parts"
        )
        
        # Report retrieval
        self.router.add_api_route(
            "/reports/{report_id}",
            self.get_analysis_report,
            methods=["GET"],
            response_model=APIResponse,
            status_code=200,
            summary="Get analysis report by ID"
        )

    async def analyze_image(
        self, 
        image: UploadFile = File(..., description="Medical image to analyze"),
        background_tasks: BackgroundTasks = BackgroundTasks(),
        db: AsyncSession = Depends(get_db)
    ) -> APIResponse:
        """Analyze a single medical image with automatic body part detection"""
        return await self.service.predict(image, background_tasks, db)

    async def analyze_image_with_body_part(
        self,
        image: UploadFile = File(..., description="Medical image to analyze"),
        body_part: str = Query(..., 
                             description="Specify body part (e.g. 'arm', 'leg', 'chest')",
                             example="arm"),
        background_tasks: BackgroundTasks = BackgroundTasks(),
        db: AsyncSession = Depends(get_db)
    ) -> APIResponse:
        """Analyze a single medical image with specified body part"""
        return await self.service.predict(image, background_tasks, db, body_part)

    async def analyze_batch(
        self, 
        images: List[UploadFile] = File(..., description="Multiple medical images to analyze"),
        background_tasks: BackgroundTasks = BackgroundTasks(),
        db: AsyncSession = Depends(get_db)
    ) -> APIResponse:
        """Analyze multiple medical images with automatic body part detection"""
        return await self.service.predict_batch(images, background_tasks, db)

    async def analyze_batch_with_body_parts(
        self,
        images: List[UploadFile] = File(..., description="Multiple medical images to analyze"),
        body_parts: str = Query(..., 
                            description="Comma-separated body parts corresponding to images",
                            example="arm,leg,chest"),
        background_tasks: BackgroundTasks = BackgroundTasks(),
        db: AsyncSession = Depends(get_db)
    ) -> APIResponse:
        """Analyze multiple medical images with specified body parts"""
        body_part_list = [bp.strip() for bp in body_parts.split(",")]
        return await self.service.predict_batch(images, background_tasks, db, body_part_list)

    async def get_analysis_report(
        self, 
        report_id: UUID = Path(..., description="Analysis report ID to retrieve"),
        db: AsyncSession = Depends(get_db)
    ) -> APIResponse:
        """Retrieve analysis results by report ID"""
        try:
            return await self.service.get_prediction_report(report_id, db)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
