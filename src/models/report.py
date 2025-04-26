from src.database import Base
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

class Report(Base):
    __tablename__ = 'reports'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    filename = Column(String, nullable=False)
    format = Column(String, nullable=False)
    received_time = Column(DateTime, nullable=False)
    model_time_seconds = Column(Float, nullable=False)
    body_part = Column(String, nullable=False)
    confidence = Column(Float, nullable=True)
    prediction = Column(String, nullable=False)
    fracture_confidence = Column(Float, nullable=True)
    error = Column(String, nullable=True)
    status = Column(String, default='In Progress') 
