from pydantic import BaseModel
from typing import List

class HealthStatus(BaseModel):
    service: str
    status: str  # 'healthy', 'degraded', 'unhealthy'
    details: str

class ModelStatus(BaseModel):
    status: str
    missing_models: List[str]
    details: str

class HealthCheckResponse(BaseModel):
    model_status: ModelStatus
    service_status: HealthStatus

class ModelStatusResponse(BaseModel):
    status: str
    missing_models: List[str]
    details: str

class FullHealthCheckResponse(BaseModel):
    services: List[HealthStatus]
