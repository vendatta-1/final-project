   # r.body_part AS model_name,
   #      COUNT(*)::INT AS used_count,
   #      COUNT(CASE WHEN r.prediction = 'Fracture' THEN 1 END)::INT AS fracture_count,
   #      COUNT(CASE WHEN r.prediction = 'No Fracture' THEN 1 END)::INT AS non_fracture_count,
   #      AVG(r.model_time_seconds) AS mean_time,
   #      AVG(r.confidence) AS part_confidence_mean,
   #      AVG(r.fracture_confidence) AS fracture_confidence_mean,
   #      COUNT(CASE WHEN r.error IS NOT NULL THEN 1 END)::INT AS error_count
   
from sqlalchemy import Column, Integer, Float, String
from sqlalchemy.dialects.postgresql import CITEXT
from src.database import Base
class ModelStatistics(Base):
   __abstract__ = True

   model_name = Column(CITEXT)
   used_count = Column(Integer)
   fracture_count = Column(Integer)
   non_fracture_count = Column(Integer)
   error_count = Column(Integer)
   mean_time = Column(Float)
   mean_part_confidence= Column(Float)
   mean_fracture_confidence = Column(Float)

   def __repr__(self):
      return (
         f"<ModelStatistics(model_name={self.model_name}, "
         f"used_count={self.used_count}, fracture_count={self.fracture_count}, "
         f"non_fracture_count={self.non_fracture_count}, error_count={self.error_count}, "
         f"mean_time={self.mean_time:.2f}, part_confidence_mean={self.mean_part_confidence:.2f}, "
         f"fracture_confidence_mean={self.mean_fracture_confidence:.2f})>"
      )

   def __str__(self):
      return (
         f"Model Name: {self.model_name}\n"
         f"Used Count: {self.used_count}\n"
         f"Fracture Count: {self.fracture_count}\n"
         f"Non-Fracture Count: {self.non_fracture_count}\n"
         f"Error Count: {self.error_count}\n"
         f"Average Time (s): {self.mean_time:.2f}\n"
         f"Mean Part Confidence: {self.mean_part_confidence:.2f}\n"
         f"Mean Fracture Confidence: {self.mean_fracture_confidence:.2f}"
      )
