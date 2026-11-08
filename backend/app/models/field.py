from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.farmer import utcnow


class Field(Base):
    __tablename__ = "fields"

    field_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    farmer_id: Mapped[str] = mapped_column(ForeignKey("farmers.farmer_id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    field_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    location_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    crop_type: Mapped[str] = mapped_column(String(80))
    area_hectares: Mapped[Optional[float]] = mapped_column(Float)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    farmer: Mapped["Farmer"] = relationship(back_populates="fields")  # noqa: F821
    sensors: Mapped[List["Sensor"]] = relationship(back_populates="field")  # noqa: F821
    sensor_readings: Mapped[List["SensorReading"]] = relationship(back_populates="field")  # noqa: F821
    weather_records: Mapped[List["WeatherData"]] = relationship(back_populates="field")  # noqa: F821
    crops: Mapped[List["Crop"]] = relationship(back_populates="field")  # noqa: F821
    schedules: Mapped[List["IrrigationSchedule"]] = relationship(
        "IrrigationSchedule", back_populates="field", cascade="all, delete-orphan"
    )


@event.listens_for(Field, "init")
def _field_init(target, args, kwargs):
    if "name" in kwargs and "field_name" not in kwargs:
        kwargs["field_name"] = kwargs["name"]
    elif "field_name" in kwargs and "name" not in kwargs:
        kwargs["name"] = kwargs["field_name"]
    if "location_name" in kwargs and "location" not in kwargs:
        kwargs["location"] = kwargs["location_name"]
    elif "location" in kwargs and "location_name" not in kwargs:
        kwargs["location_name"] = kwargs["location"]


@event.listens_for(Field, "before_insert")
@event.listens_for(Field, "before_update")
def _sync_field_aliases(mapper, connection, target):
    if target.field_name is None and target.name is not None:
        target.field_name = target.name
    elif target.name is None and target.field_name is not None:
        target.name = target.field_name
    if target.location is None and target.location_name is not None:
        target.location = target.location_name
    elif target.location_name is None and target.location is not None:
        target.location_name = target.location
