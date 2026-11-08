"""Persist data-quality events and compute summary statistics. Never invents values."""
import json
from typing import Any, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import DataQualityEvent, SensorReading, WeatherData


def record_event(
    db: Session,
    event_type: str,
    source: str,
    message: str,
    sensor_id: Optional[str] = None,
    field_id: Optional[str] = None,
    details: Any = None,
) -> None:
    payload = None
    if details is not None:
        try:
            payload = json.dumps(details, default=str)[:4000]
        except (TypeError, ValueError):
            payload = str(details)[:4000]
    db.add(
        DataQualityEvent(
            event_type=event_type,
            source=source,
            sensor_id=sensor_id,
            field_id=field_id,
            message=message[:400],
            details=payload,
        )
    )
    db.commit()


def list_events(db: Session, limit: int = 100, event_type: Optional[str] = None) -> List[DataQualityEvent]:
    stmt = select(DataQualityEvent).order_by(DataQualityEvent.created_at.desc()).limit(limit)
    if event_type:
        stmt = stmt.where(DataQualityEvent.event_type == event_type)
    return list(db.scalars(stmt))


def stats(db: Session) -> dict:
    stored = db.scalar(select(func.count()).select_from(SensorReading)) or 0
    simulated = db.scalar(select(func.count()).select_from(SensorReading).where(SensorReading.is_simulated.is_(True))) or 0
    out_of_order = db.scalar(
        select(func.count()).select_from(SensorReading).where(SensorReading.quality_flags.contains("out_of_order"))
    ) or 0
    weather_rows = db.scalar(select(func.count()).select_from(WeatherData)) or 0
    weather_mock = db.scalar(select(func.count()).select_from(WeatherData).where(WeatherData.is_mock.is_(True))) or 0

    event_counts = dict(
        db.execute(
            select(DataQualityEvent.event_type, func.count()).group_by(DataQualityEvent.event_type)
        ).all()
    )
    source_counts = dict(
        db.execute(select(DataQualityEvent.source, func.count()).group_by(DataQualityEvent.source)).all()
    )
    failures = db.scalar(select(func.count()).select_from(DataQualityEvent)) or 0
    weather_failures = source_counts.get("weather", 0)

    return {
        "readings_stored": stored,
        "valid_readings": stored,  # invalid readings are rejected, not stored
        "simulated_readings": simulated,
        "out_of_order_stored": out_of_order,
        "ingestion_failures": failures,
        "invalid_readings": event_counts.get("out_of_range", 0)
        + event_counts.get("not_numeric", 0)
        + event_counts.get("not_finite", 0)
        + event_counts.get("validation_failed", 0),
        "missing_value_count": event_counts.get("missing_value", 0),
        "duplicate_count": event_counts.get("duplicate", 0),
        "out_of_range_count": event_counts.get("out_of_range", 0),
        "invalid_timestamp_count": event_counts.get("invalid_timestamp", 0) + event_counts.get("future_timestamp", 0),
        "weather_observations": weather_rows,
        "weather_mock_observations": weather_mock,
        "weather_ingestion_failures": weather_failures,
        "events_by_type": event_counts,
        "events_by_source": source_counts,
        "notes": [
            "Invalid readings are rejected and not stored.",
            "Missing values are not imputed.",
            "Zero is a real measurement; missing is recorded as an event, never as 0.",
        ],
    }
