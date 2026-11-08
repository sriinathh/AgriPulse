from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.farmer import utcnow


class DataQualityEvent(Base):
    __tablename__ = "data_quality_events"
    __table_args__ = (
        Index("ix_dq_created", "created_at"),
        Index("ix_dq_type", "event_type"),
    )

    event_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(40))  # missing_value, out_of_range, duplicate, ...
    source: Mapped[str] = mapped_column(String(20))  # rest, mqtt, weather, demo
    sensor_id: Mapped[Optional[str]] = mapped_column(String(32))
    field_id: Mapped[Optional[str]] = mapped_column(String(32))
    message: Mapped[str] = mapped_column(String(400))
    details: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
