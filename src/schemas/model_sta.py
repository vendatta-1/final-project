from typing import List, Optional
from pydantic import BaseModel

class ModelStatisticsBase(BaseModel):
    model_name: str
    used_count: int
    fracture_count: int
    non_fracture_count: int 
    mean_part_confidence: float
    mean_fracture_confidence: float
    mean_time: float
    error_count: Optional[int]

    class Config:
        orm_mode = True
        from_attributes = True
        validate_by_name = True
 
class ModelStatisticsResponse(ModelStatisticsBase):
    pass
 
class AllModelsStatisticsResponse(BaseModel):
    models: List[ModelStatisticsResponse]
