from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.farmer import ID_PATTERN
from app.schemas.field import _normalise_crop


class CropCreate(BaseModel):
    crop_id: Optional[str] = Field(None, pattern=ID_PATTERN)
    field_id: str = Field(pattern=ID_PATTERN)
    crop_type: str = Field(max_length=80)
    variety: Optional[str] = Field(None, max_length=80)
    planting_date: Optional[date] = None
    growth_stage: Optional[str] = Field(None, max_length=40)
    notes: Optional[str] = Field(None, max_length=400)

    @field_validator("crop_type")
    @classmethod
    def _crop(cls, v: str) -> str:
        return _normalise_crop(v)


class CropPatch(BaseModel):
    crop_type: Optional[str] = Field(None, max_length=80)
    variety: Optional[str] = Field(None, max_length=80)
    planting_date: Optional[date] = None
    growth_stage: Optional[str] = Field(None, max_length=40)
    notes: Optional[str] = Field(None, max_length=400)
    field_id: Optional[str] = Field(None, pattern=ID_PATTERN)

    @field_validator("crop_type")
    @classmethod
    def _crop(cls, v: Optional[str]) -> Optional[str]:
        return _normalise_crop(v) if v is not None else v


class CropOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    crop_id: str
    field_id: str
    crop_type: str
    variety: Optional[str]
    planting_date: Optional[date]
    growth_stage: Optional[str]
    notes: Optional[str]
    is_demo: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
