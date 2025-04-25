from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ReportCreate(BaseModel):
    id: Optional[str] = None
    filename: str
    format: str
    received_time: datetime
    model_time_seconds: float
    body_part: str
    confidence: Optional[float]
    prediction: str
    fracture_confidence: Optional[float] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True
        validate_by_name = True
        allow_arbitrary_types = True
