from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.farmer import utcnow


class WeatherData(Base):
    __tablename__ = "weather_data"
    __table_args__ = (
        UniqueConstraint("field_id", "timestamp", name="uq_weather_field_ts"),
        Index("ix_weather_field_ts", "field_id", "timestamp"),
        Index("ix_weather_field_id", "field_id"),
        Index("ix_weather_timestamp", "timestamp"),
    )

    weather_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    field_id: Mapped[str] = mapped_column(ForeignKey("fields.field_id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime)  # observation time from provider, naive UTC
    temperature: Mapped[float] = mapped_column()  # deg C
    humidity: Mapped[float] = mapped_column()  # % relative humidity
    rainfall: Mapped[float] = mapped_column()  # mm in the last hour
    wind_speed: Mapped[Optional[float]] = mapped_column()  # m/s
    condition: Mapped[Optional[str]] = mapped_column(String(120))
    source: Mapped[str] = mapped_column(String(40), default="openweathermap")
    is_mock: Mapped[bool] = mapped_column(Boolean, default=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    field: Mapped["Field"] = relationship(back_populates="weather_records")  # noqa: F821
