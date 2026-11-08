from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.farmer import utcnow


class SensorReading(Base):
    __tablename__ = "sensor_readings"
    __table_args__ = (
        UniqueConstraint("sensor_id", "timestamp", name="uq_reading_sensor_ts"),  # blocks duplicates
        Index("ix_reading_field_ts", "field_id", "timestamp"),
        Index("ix_reading_sensor_ts", "sensor_id", "timestamp"),
        Index("ix_reading_sensor_id", "sensor_id"),
        Index("ix_reading_field_id", "field_id"),
        Index("ix_reading_timestamp", "timestamp"),
    )

    reading_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sensor_id: Mapped[str] = mapped_column(ForeignKey("sensors.sensor_id"))
    field_id: Mapped[str] = mapped_column(ForeignKey("fields.field_id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime)  # naive UTC
    soil_moisture: Mapped[Optional[float]] = mapped_column()  # volumetric %, 0-100
    measurement_type: Mapped[str] = mapped_column(String(40), default="soil_moisture")
    value: Mapped[Optional[float]] = mapped_column()
    unit: Mapped[Optional[str]] = mapped_column(String(32))
    quality_status: Mapped[str] = mapped_column(String(32), default="valid")
    quality_flags: Mapped[Optional[str]] = mapped_column(String(500))
    temperature: Mapped[Optional[float]] = mapped_column()
    humidity: Mapped[Optional[float]] = mapped_column()
    soil_ph: Mapped[Optional[float]] = mapped_column()
    rainfall: Mapped[Optional[float]] = mapped_column()
    water_level: Mapped[Optional[float]] = mapped_column()
    flow_rate: Mapped[Optional[float]] = mapped_column()
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    sensor: Mapped["Sensor"] = relationship(back_populates="readings")  # noqa: F821
    field: Mapped["Field"] = relationship(back_populates="sensor_readings")  # noqa: F821
