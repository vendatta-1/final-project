from pydantic import BaseModel
from typing import Optional, TypeVar, Generic
from datetime import datetime
from uuid import UUID

class ReportBase(BaseModel):
    id: Optional[UUID]
    status: str

    class Config:
        orm_mode = True
        from_attributes = True
        validate_by_name = True
        allow_arbitrary_types = True
        json_encoders = {
            UUID: lambda v: str(v)  
        }

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
    class Config:
        json_encoders = {
            UUID: lambda v: str(v)  
        }

T = TypeVar("T")





class APIResponse(BaseModel, Generic[T]):
    error_message: Optional[str] = None
    is_success: bool = False
    status_code: str
    data: Optional[T] = None
    class Config:
        json_encoders = {
            UUID: lambda v: str(v)  
        }