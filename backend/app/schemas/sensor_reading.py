"""Sensor reading contract (shared with the Week 3 ML module).

  {"sensor_id": "SM001", "field_id": "F001", "timestamp": "2026-10-07T10:30:00", "soil_moisture": 35.6}

`timestamp`, `soil_moisture` and extra measurements are deliberately typed `Any` here: the cleaning layer, not Pydantic,
decides what is acceptable so that null/garbage values get a precise, uniform error report.
"""
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.farmer import ID_PATTERN


class SensorReadingIn(BaseModel):
    model_config = ConfigDict(extra="ignore")
    sensor_id: str = Field(pattern=ID_PATTERN)
    field_id: Optional[str] = Field(None, pattern=ID_PATTERN, description="Optional; if given it must match the sensor's field")
    timestamp: Any = Field(None, description="ISO-8601. If omitted the server receive time (UTC) is used and flagged.")
    soil_moisture: Any = Field(None, description="Volumetric %, 0-100")
    measurement_type: Optional[str] = Field(None, description="Defaults to the sensor's type")
    value: Any = Field(None, description="Primary measurement when not using soil_moisture")
    unit: Optional[str] = None
    temperature: Any = None
    humidity: Any = None
    soil_ph: Any = None
    rainfall: Any = None
    water_level: Any = None
    flow_rate: Any = None
    is_simulated: bool = Field(False, description="True for generated/test data, never for real hardware")


class SensorReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    reading_id: int
    sensor_id: str
    field_id: str
    timestamp: datetime
    soil_moisture: Optional[float] = None
    measurement_type: Optional[str] = "soil_moisture"
    value: Optional[float] = None
    unit: Optional[str] = None
    quality_status: Optional[str] = "valid"
    quality_flags: Optional[str] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    soil_ph: Optional[float] = None
    rainfall: Optional[float] = None
    water_level: Optional[float] = None
    flow_rate: Optional[float] = None
    is_simulated: Optional[bool] = False
    flow_rate: Optional[float] = None
    is_simulated: bool


class CleaningReport(BaseModel):
    timestamp_source: str
    notes: List[str]


class IngestResponse(BaseModel):
    status: str
    reading: SensorReadingOut
    cleaning: CleaningReport
