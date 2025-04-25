from fastapi import APIRouter, File, UploadFile
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from src.services import Service
from src.schemas import ReportCreate

class ModelRoutes:
    
    def __init__(self):
        self.router = APIRouter()
        self.router.add_api_route("/api/", self.receive_image, methods=["POST"], response_model=ReportCreate, status_code=200)

    async def receive_image(self, image: UploadFile):

            service = Service()
            report = service.predict(image)

            return JSONResponse(content=jsonable_encoder(report))
