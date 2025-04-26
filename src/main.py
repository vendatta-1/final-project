from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from src.routes import ModelRoutes
from  src.logger import logger
app = FastAPI(
    redoc_url=None,
    docs_url="/swagger",
    root_path="/api/v1",
    openapi_url="/openapi.json",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.log("INFO", "API started")

# @app.get("/",include_in_schema=False)
# async def root():
#     return RedirectResponse(url="/api/v1/swagger")

app.include_router(ModelRoutes().router)