"""Sensor ingestion: lookup -> validate/clean -> persist. No HTTP/routing code here."""
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings
from app.errors import AppError
from app.models import SensorReading
from app.models.farmer import utcnow
from app.schemas.sensor_reading import SensorReadingIn
from app.services import quality_service, registry_service as registry
from app.services.data_cleaning_service import CleanedReading, DataValidationError, clean_sensor_reading

log = logging.getLogger("irrigation.ingest")

EXTRA_FIELDS = ("temperature", "humidity", "soil_ph", "rainfall", "water_level", "flow_rate")


def _extras(payload: SensorReadingIn) -> dict:
    return {name: getattr(payload, name) for name in EXTRA_FIELDS if getattr(payload, name) is not None}


def ingest_reading(db: Session, payload: SensorReadingIn, settings: Settings, source: str = "rest"):
    sensor = registry.get_sensor_or_404(db, payload.sensor_id)

    if payload.field_id is not None and payload.field_id != sensor.field_id:
        quality_service.record_event(
            db, "field_mismatch", source,
            f"Sensor '{sensor.sensor_id}' field mismatch.",
            sensor_id=sensor.sensor_id, field_id=payload.field_id,
        )
        raise AppError(422, "field_mismatch",
                       f"Sensor '{sensor.sensor_id}' belongs to field '{sensor.field_id}', not '{payload.field_id}'.")
    if sensor.status != "active":
        quality_service.record_event(
            db, "sensor_inactive", source,
            f"Sensor '{sensor.sensor_id}' is inactive.",
            sensor_id=sensor.sensor_id, field_id=sensor.field_id,
        )
        raise AppError(409, "sensor_inactive", f"Sensor '{sensor.sensor_id}' is {sensor.status}; readings are not accepted.")

    extras = _extras(payload)
    mtype = payload.measurement_type or sensor.sensor_type or "soil_moisture"
    require_moisture = mtype == "soil_moisture" and not extras and payload.value is None
    try:
        cleaned: CleanedReading = clean_sensor_reading(
            payload.soil_moisture, payload.timestamp,
            future_tolerance_seconds=settings.sensor_future_tolerance_seconds,
            extras=extras,
            measurement_type=mtype,
            value=payload.value,
            require_soil_moisture=require_moisture or (payload.soil_moisture is not None or mtype == "soil_moisture" and payload.value is None and not extras),
        )
    except DataValidationError as exc:
        details = [i.as_dict() for i in exc.issues]
        codes = {i.code for i in exc.issues}
        event_type = next(iter(codes), "validation_failed")
        quality_service.record_event(
            db, event_type, source, "Reading rejected; nothing was stored.",
            sensor_id=payload.sensor_id, field_id=sensor.field_id, details=details,
        )
        log.warning("Ingestion rejected sensor_id=%s source=%s codes=%s", payload.sensor_id, source, sorted(codes))
        raise AppError(422, "validation_failed", "Reading rejected; nothing was stored.", details)

    flags: List[str] = []
    last = db.scalar(
        select(SensorReading)
        .where(SensorReading.sensor_id == sensor.sensor_id)
        .order_by(SensorReading.timestamp.desc())
        .limit(1)
    )
    if last is not None and cleaned.timestamp < last.timestamp:
        flags.append("out_of_order")
        cleaned.notes.append("timestamp is earlier than the previously stored reading (stored and flagged)")

    reading = SensorReading(
        sensor_id=sensor.sensor_id, field_id=sensor.field_id,
        timestamp=cleaned.timestamp, soil_moisture=cleaned.soil_moisture,
        measurement_type=cleaned.measurement_type,
        value=cleaned.value if cleaned.value is not None else cleaned.soil_moisture,
        unit=payload.unit or cleaned.unit,
        quality_status="valid",
        quality_flags=",".join(flags) if flags else None,
        temperature=cleaned.extras.get("temperature"),
        humidity=cleaned.extras.get("humidity"),
        soil_ph=cleaned.extras.get("soil_ph"),
        rainfall=cleaned.extras.get("rainfall"),
        water_level=cleaned.extras.get("water_level"),
        flow_rate=cleaned.extras.get("flow_rate"),
        is_simulated=payload.is_simulated,
    )
    db.add(reading)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        quality_service.record_event(
            db, "duplicate", source,
            f"Duplicate reading for sensor '{sensor.sensor_id}'.",
            sensor_id=sensor.sensor_id, field_id=sensor.field_id,
            details={"timestamp": cleaned.timestamp.isoformat()},
        )
        raise AppError(409, "duplicate_reading",
                       f"Sensor '{sensor.sensor_id}' already has a reading at {cleaned.timestamp.isoformat()}.")
    sensor.last_seen_at = utcnow()
    db.commit()
    return reading, cleaned


def list_readings(db: Session, sensor_id: Optional[str], field_id: Optional[str],
                  start: Optional[datetime], end: Optional[datetime], limit: int,
                  measurement_type: Optional[str] = None, offset: int = 0,
                  order: str = "desc") -> List[SensorReading]:
    stmt = select(SensorReading)
    if sensor_id:
        stmt = stmt.where(SensorReading.sensor_id == sensor_id)
    # If a specific sensor is requested, its field is implicit; ignore field filter to avoid mismatches.
    if field_id and not sensor_id:
        stmt = stmt.where(SensorReading.field_id == field_id)
    if start:
        stmt = stmt.where(SensorReading.timestamp >= start)
    if end:
        stmt = stmt.where(SensorReading.timestamp <= end)
    if measurement_type:
        # Use case‑insensitive comparison to match stored values like "temperature" with UI values like "Temperature"
        from sqlalchemy import func
        stmt = stmt.where(func.lower(SensorReading.measurement_type) == measurement_type.lower())
    order_clause = SensorReading.timestamp.asc() if str(order).lower() == "asc" else SensorReading.timestamp.desc()
    return list(db.scalars(stmt.order_by(order_clause).offset(offset).limit(limit)))
