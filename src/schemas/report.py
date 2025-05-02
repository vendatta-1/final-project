from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from src.schemas.services_schema import APIResponse

class ReportBase(BaseModel):
    id: Optional[UUID]
    status: str

    class Config:
        orm_mode = True
        from_attributes = True
        validate_by_name = True
        allow_arbitrary_types = True
        

class ReportCreate(ReportBase):
    filename: Optional[str] = None
    format: Optional[str] = None
    received_time: datetime
    model_time_seconds: float
    body_part: str
    confidence: Optional[float]
    prediction: str
    fracture_confidence: Optional[float] = None
    error: Optional[str] = None

class ReportResponse(ReportBase):
    pass

# Correct inheritance
class ReportCompleteResponse(ReportCreate):
    pass
