from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.farmer import ID_PATTERN, FarmerOut
from app.schemas.sensor import SensorOut


def _normalise_crop(value: str) -> str:
    value = " ".join(value.split())
    if not value:
        raise ValueError("crop_type must not be empty")
    return value.title()


class FieldCreate(BaseModel):
    field_id: Optional[str] = Field(None, pattern=ID_PATTERN, description="Optional; auto-generated (F001...) if omitted")
    farmer_id: str = Field(pattern=ID_PATTERN)
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    field_name: Optional[str] = Field(None, min_length=1, max_length=120)
    location_name: Optional[str] = Field(None, max_length=200)
    location: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    crop_type: str = Field(max_length=80)
    area_hectares: Optional[float] = Field(None, gt=0)

    @field_validator("crop_type")
    @classmethod
    def _crop(cls, v: str) -> str:
        return _normalise_crop(v)

    @model_validator(mode="after")
    def _coords_together(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be provided together")
        if not self.name and not self.field_name:
            raise ValueError("name or field_name must be provided")
        if not self.name:
            self.name = self.field_name
        if not self.field_name:
            self.field_name = self.name
        if not self.location_name and self.location:
            self.location_name = self.location
        if not self.location and self.location_name:
            self.location = self.location_name
        return self


class FieldUpdate(BaseModel):
    farmer_id: Optional[str] = Field(None, pattern=ID_PATTERN)
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    field_name: Optional[str] = Field(None, min_length=1, max_length=120)
    location_name: Optional[str] = Field(None, max_length=200)
    location: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    crop_type: Optional[str] = Field(None, max_length=80)
    area_hectares: Optional[float] = Field(None, gt=0)

    @field_validator("crop_type")
    @classmethod
    def _crop(cls, v: Optional[str]) -> Optional[str]:
        return _normalise_crop(v) if v is not None else v

    @model_validator(mode="after")
    def _coords_together(self):
        if self.latitude is not None and self.longitude is None:
            raise ValueError("latitude and longitude must be provided together")
        if self.longitude is not None and self.latitude is None:
            raise ValueError("latitude and longitude must be provided together")
        if self.field_name and not self.name:
            self.name = self.field_name
        elif self.name and not self.field_name:
            self.field_name = self.name
        if self.location and not self.location_name:
            self.location_name = self.location
        elif self.location_name and not self.location:
            self.location = self.location_name
        return self


class CropUpdate(BaseModel):
    crop_type: str = Field(max_length=80)

    @field_validator("crop_type")
    @classmethod
    def _crop(cls, v: str) -> str:
        return _normalise_crop(v)


class FieldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    field_id: str
    farmer_id: str
    name: str
    field_name: Optional[str] = None
    location_name: Optional[str] = None
    location: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    crop_type: str
    area_hectares: Optional[float] = None
    is_demo: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None


class FieldDetail(FieldOut):
    sensors: List[SensorOut] = []


class FarmerDetail(FarmerOut):
    fields: List[FieldOut] = []
