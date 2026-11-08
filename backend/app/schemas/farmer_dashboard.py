"""Pydantic schema for farmer dashboard response.

All fields are optional where a value may not be calculable (e.g., no sensor data)."""

from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class WeatherSummary(BaseModel):
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    rainfall: Optional[float] = None
    timestamp: Optional[datetime] = None

class FarmerDashboardResponse(BaseModel):
    farmer_name: Optional[str] = None
    farmer_email: Optional[str] = None
    total_fields: int
    fields_needing_irrigation: int
    average_soil_moisture: Optional[float] = None
    total_water_used_liters: float
    weather_summary: Optional[WeatherSummary] = None
