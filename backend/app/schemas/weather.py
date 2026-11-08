"""Weather contract (shared with the Week 3 ML module).

  {"field_id": "F001", "timestamp": "2026-10-07T10:30:00", "temperature": 29.0, "humidity": 68, "rainfall": 2.1}

temperature = deg C, humidity = % RH, rainfall = mm in the last hour,
timestamp = provider observation time (UTC), fetched_at = when the API call was made.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class WeatherOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    weather_id: int
    field_id: str
    timestamp: datetime           # provider observation time (UTC)
    fetched_at: Optional[datetime] = None  # when our backend called the API
    temperature: float
    humidity: float
    rainfall: float
    wind_speed: Optional[float] = None
    condition: Optional[str] = None
    source: str
    is_mock: bool = False


class WeatherFetchResponse(BaseModel):
    status: str  # "stored" (new record) | "already_stored" (provider returned an observation we already have)
    weather: WeatherOut
    mock: bool = False
    requested_coordinates: Optional[dict] = None
    provider_coordinates: Optional[dict] = None
    provider_location: Optional[str] = None


class PlaceOut(BaseModel):
    """Geocoding result from OpenWeatherMap."""
    name: str
    state: Optional[str] = None
    country: Optional[str] = None
    latitude: float
    longitude: float
    label: str


class SearchedWeatherOut(BaseModel):
    """Live weather observation for an arbitrary searched location (not persisted to any field)."""
    model_config = ConfigDict(from_attributes=True)
    latitude: float
    longitude: float
    location_name: Optional[str] = None
    timestamp: datetime           # provider observation time (UTC)
    fetched_at: datetime          # when our backend called the API (UTC)
    temperature: float
    humidity: float
    rainfall: float
    wind_speed: Optional[float] = None
    condition: Optional[str] = None
    source: str = "openweathermap"
    is_mock: bool = False
    provider_coordinates: Optional[dict] = None
    provider_location: Optional[str] = None


