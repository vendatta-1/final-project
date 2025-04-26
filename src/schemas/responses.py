from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class ReportCreate(BaseModel):
    id: Optional[UUID] = None
    filename:Optional[ str] =None
    format:Optional[ str]=None
    received_time: datetime
    model_time_seconds: float
    body_part: str
    confidence: Optional[float]
    prediction: str
    fracture_confidence: Optional[float] = None
    error: Optional[str] = None
    status: Optional[str]

    class Config:
        from_attributes = True
        validate_by_name = True
        allow_arbitrary_types = True
