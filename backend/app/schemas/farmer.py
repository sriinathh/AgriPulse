from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

ID_PATTERN = r"^[A-Za-z0-9_-]{1,32}$"


class FarmerCreate(BaseModel):
    farmer_id: Optional[str] = Field(None, pattern=ID_PATTERN, description="Optional; auto-generated (FR001...) if omitted")
    name: str = Field(min_length=1, max_length=120)
    phone: Optional[str] = Field(None, max_length=32)
    email: Optional[str] = Field(None, max_length=160)


class FarmerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    phone: Optional[str] = Field(None, max_length=32)
    email: Optional[str] = Field(None, max_length=160)


class FarmerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    farmer_id: str
    name: str
    phone: Optional[str]
    email: Optional[str]
    is_demo: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
