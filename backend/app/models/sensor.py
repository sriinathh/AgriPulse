from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.farmer import utcnow


class Sensor(Base):
    __tablename__ = "sensors"

    sensor_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    field_id: Mapped[str] = mapped_column(ForeignKey("fields.field_id"), index=True)
    sensor_type: Mapped[str] = mapped_column(String(40), default="soil_moisture")
    measurement_type: Mapped[Optional[str]] = mapped_column(String(40), default="soil_moisture")
    unit: Mapped[Optional[str]] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | inactive
    connectivity_mode: Mapped[Optional[str]] = mapped_column(String(32), default="cellular")
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    field: Mapped["Field"] = relationship(back_populates="sensors")  # noqa: F821
    readings: Mapped[List["SensorReading"]] = relationship(back_populates="sensor")  # noqa: F821


@event.listens_for(Sensor, "init")
def _sensor_init(target, args, kwargs):
    if "sensor_type" in kwargs and "measurement_type" not in kwargs:
        kwargs["measurement_type"] = kwargs["sensor_type"]
    elif "measurement_type" in kwargs and "sensor_type" not in kwargs:
        kwargs["sensor_type"] = kwargs["measurement_type"]


@event.listens_for(Sensor, "before_insert")
@event.listens_for(Sensor, "before_update")
def _sync_sensor_aliases(mapper, connection, target):
    if target.measurement_type is None and target.sensor_type is not None:
        target.measurement_type = target.sensor_type
    elif target.sensor_type is None and target.measurement_type is not None:
        target.sensor_type = target.measurement_type
    if not target.connectivity_mode:
        target.connectivity_mode = "cellular"
