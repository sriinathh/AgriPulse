'''Pydantic schemas for IrrigationSchedule'''

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field as PydanticField

class ScheduleStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    skipped = "skipped"

class IrrigationScheduleBase(BaseModel):
    field_id: str = PydanticField(..., description="Foreign key to fields.field_id")
    recommended_date: datetime = PydanticField(..., description="Date of recommended irrigation")
    recommended_time: str = PydanticField(..., description="Time of day, e.g., '06:30'")
    duration_minutes: float = PydanticField(..., gt=0, description="Length of irrigation in minutes")
    water_quantity_liters: float = PydanticField(..., gt=0, description="Estimated water amount")
    priority: Optional[str] = PydanticField(None, description="Optional priority label")
    reason: Optional[str] = PydanticField(None, description="Reason for recommendation")

class IrrigationScheduleCreate(IrrigationScheduleBase):
    pass

class IrrigationScheduleOut(IrrigationScheduleBase):
    schedule_id: str = PydanticField(..., description="Primary key of the schedule")
    status: ScheduleStatus = PydanticField(default=ScheduleStatus.pending)
    created_at: datetime = PydanticField(...)
    updated_at: datetime = PydanticField(...)

    class Config:
        from_attributes = True

class IrrigationScheduleStatusUpdate(BaseModel):
    status: ScheduleStatus = PydanticField(..., description="New status for the schedule")
