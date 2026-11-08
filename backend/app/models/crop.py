from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.farmer import utcnow


class Crop(Base):
    __tablename__ = "crops"

    crop_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    field_id: Mapped[str] = mapped_column(ForeignKey("fields.field_id"), index=True)
    crop_type: Mapped[str] = mapped_column(String(80))
    variety: Mapped[Optional[str]] = mapped_column(String(80))
    planting_date: Mapped[Optional[date]] = mapped_column(Date)
    growth_stage: Mapped[Optional[str]] = mapped_column(String(40))
    notes: Mapped[Optional[str]] = mapped_column(String(400))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    field: Mapped["Field"] = relationship(back_populates="crops")  # noqa: F821
