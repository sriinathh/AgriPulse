from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.farmer import ID_PATTERN

SENSOR_TYPES = Literal[
    "soil_moisture", "temperature", "humidity", "soil_ph", "rainfall", "water_level", "flow_rate"
]


class SensorCreate(BaseModel):
    sensor_id: Optional[str] = Field(None, pattern=ID_PATTERN, description="Optional; auto-generated (SM001...) if omitted")
    field_id: str = Field(pattern=ID_PATTERN)
    sensor_type: Optional[str] = "soil_moisture"
    measurement_type: Optional[str] = None
    unit: Optional[str] = Field(None, max_length=32)
    status: Literal["active", "inactive"] = "active"
    connectivity_mode: Optional[str] = "cellular"
    is_simulated: bool = False

    @model_validator(mode="after")
    def _sync_types(self):
        if self.measurement_type and not self.sensor_type:
            self.sensor_type = self.measurement_type
        elif self.sensor_type and not self.measurement_type:
            self.measurement_type = self.sensor_type
        return self


class SensorUpdate(BaseModel):
    field_id: Optional[str] = Field(None, pattern=ID_PATTERN)
    sensor_type: Optional[str] = None
    measurement_type: Optional[str] = None
    unit: Optional[str] = Field(None, max_length=32)
    status: Optional[Literal["active", "inactive"]] = None
    connectivity_mode: Optional[str] = None

    @model_validator(mode="after")
    def _sync_types(self):
        if self.measurement_type and not self.sensor_type:
            self.sensor_type = self.measurement_type
        elif self.sensor_type and not self.measurement_type:
            self.measurement_type = self.sensor_type
        return self


class SensorStatusUpdate(BaseModel):
    status: Literal["active", "inactive"]


class SensorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    sensor_id: str
    field_id: str
    sensor_type: str
    measurement_type: Optional[str] = None
    unit: Optional[str] = None
    status: str
    connectivity_mode: Optional[str] = "cellular"
    last_seen_at: Optional[datetime] = None
    is_simulated: bool = False
    is_demo: bool = False
    created_at: datetime
