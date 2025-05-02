from pydantic import BaseModel

from typing import Optional, Generic, TypeVar

class PredictionResult(BaseModel):
    body_part: str
    result: str

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    error_message: Optional[str] = None
    is_success: bool = False
    status_code: str
    data: Optional[T] = None

