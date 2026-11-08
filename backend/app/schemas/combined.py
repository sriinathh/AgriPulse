"""Combined sensor + weather view: the shape the Week 3 ML feature pipeline will consume."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.field import FieldOut
from app.schemas.sensor import SensorOut
from app.schemas.weather import WeatherOut


class CombinedRecord(BaseModel):
    sensor_id: str
    timestamp: datetime
    soil_moisture: float
    is_simulated: bool
    # Latest stored weather observation at or before `timestamp` (as-of join). None if none exists yet.
    weather: Optional[WeatherOut] = None
    weather_age_minutes: Optional[float] = None


class CombinedFieldData(BaseModel):
    field: FieldOut
    sensors: List[SensorOut]
    latest_weather: Optional[WeatherOut]
    records: List[CombinedRecord]  # newest first
