from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from src.services import Service
from src.schemas import ReportCreate

class ModelRoutes:
    
    def __init__(self):
        self.router = APIRouter()
        self.router.add_api_route(
            "/api/", 
            self.receive_image, 
            methods=["POST"], 
            response_model=ReportCreate, 
            status_code=200
        )

    async def receive_image(self, image: UploadFile):
        try:
            service = Service()
            report = service.predict(image)

            if report.prediction == "Error" and report.error:
                raise HTTPException(status_code=500, detail=report.error)

            return JSONResponse(content=jsonable_encoder(report))

        except Exception as e: 
            raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
