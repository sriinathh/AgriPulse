from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base
import enum

class ScheduleStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    skipped = "skipped"

class IrrigationSchedule(Base):
    __tablename__ = "irrigation_schedule"
    schedule_id = Column(String, primary_key=True, index=True)
    field_id = Column(String, ForeignKey("fields.field_id"), nullable=False)
    recommended_date = Column(DateTime, nullable=False)
    recommended_time = Column(String, nullable=False)  # e.g., "06:30"
    duration_minutes = Column(Float, nullable=False)
    water_quantity_liters = Column(Float, nullable=False)
    priority = Column(String, nullable=True)
    reason = Column(String, nullable=True)
    status = Column(Enum(ScheduleStatus), default=ScheduleStatus.pending, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    field = relationship("Field", back_populates="schedules")
