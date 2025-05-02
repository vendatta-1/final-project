from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.routes import MedicalImageAnalysisRoutes, HealthRoutes, StatisticsRoutes
from src.logger import logger

from src.limiters import limiter

 
app = FastAPI(
    redoc_url=None,
    docs_url="/swagger",
    root_path="/v1/api",
    openapi_url="/openapi.json",
)
 


@app.on_event("startup")
async def startup():
    app.state.limiter = limiter   
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
logger.log("INFO", "API started")
 
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/v1/api/swagger")
 
app.include_router(MedicalImageAnalysisRoutes().router)
app.include_router(HealthRoutes().router)
app.include_router(StatisticsRoutes().router)

