from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database.session import get_db
from app.models import Sensor
from app.schemas.sensor import SensorCreate, SensorOut, SensorStatusUpdate, SensorUpdate
from app.schemas.sensor_reading import CleaningReport, IngestResponse, SensorReadingIn, SensorReadingOut
from app.services import registry_service as registry
from app.services import sensor_service

router = APIRouter(tags=["sensors"])


@router.post("/sensors", response_model=SensorOut, status_code=201)
def register_sensor(body: SensorCreate, db: Session = Depends(get_db)):
    return registry.create_sensor(db, body)


@router.get("/sensors", response_model=List[SensorOut])
def list_sensors(field_id: Optional[str] = None, db: Session = Depends(get_db)):
    stmt = select(Sensor).order_by(Sensor.sensor_id)
    if field_id:
        stmt = stmt.where(Sensor.field_id == field_id)
    return db.scalars(stmt).all()


@router.get("/sensors/{sensor_id}", response_model=SensorOut)
def get_sensor(sensor_id: str, db: Session = Depends(get_db)):
    return registry.get_sensor_or_404(db, sensor_id)


@router.put("/sensors/{sensor_id}", response_model=SensorOut)
def update_sensor(sensor_id: str, body: SensorUpdate, db: Session = Depends(get_db)):
    return registry.update_sensor(db, sensor_id, body)


@router.delete("/sensors/{sensor_id}", status_code=204)
def delete_sensor(sensor_id: str, db: Session = Depends(get_db)):
    registry.delete_sensor(db, sensor_id)


@router.put("/sensors/{sensor_id}/status", response_model=SensorOut)
def set_status(sensor_id: str, body: SensorStatusUpdate, db: Session = Depends(get_db)):
    return registry.set_sensor_status(db, sensor_id, body.status)


@router.post("/sensor/readings", response_model=IngestResponse, status_code=201, tags=["ingestion"])
def ingest_reading(body: SensorReadingIn, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    reading, cleaned = sensor_service.ingest_reading(db, body, settings)
    return IngestResponse(
        status="stored", reading=reading,
        cleaning=CleaningReport(timestamp_source=cleaned.timestamp_source, notes=cleaned.notes),
    )


@router.get("/sensor/readings", response_model=List[SensorReadingOut], tags=["ingestion"])
def list_readings(
    sensor_id: Optional[str] = None, field_id: Optional[str] = None,
    measurement_type: Optional[str] = None,
    start: Optional[datetime] = None, end: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order: 'asc' for chronological, 'desc' for newest first"),
    db: Session = Depends(get_db),
):
    return sensor_service.list_readings(db, sensor_id, field_id, start, end, limit, measurement_type, offset, order=order)


@router.get("/sensor/readings/export.csv", tags=["ingestion"])
def export_readings(
    sensor_id: Optional[str] = None, field_id: Optional[str] = None,
    start: Optional[datetime] = None, end: Optional[datetime] = None,
    order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order for export: 'asc' for chronological, 'desc' for newest first"),
    db: Session = Depends(get_db),
):
    rows = sensor_service.list_readings(db, sensor_id, field_id, start, end, 1000, order=order)

    def _iter():
        header = "reading_id,sensor_id,field_id,timestamp,soil_moisture,measurement_type,value,unit,quality_status,quality_flags,is_simulated\n"
        yield header
        for r in rows:
            yield (
                f"{r.reading_id},{r.sensor_id},{r.field_id},{r.timestamp.isoformat()},"
                f"{'' if r.soil_moisture is None else r.soil_moisture},{r.measurement_type},"
                f"{'' if r.value is None else r.value},{r.unit or ''},{r.quality_status},"
                f"{r.quality_flags or ''},{str(r.is_simulated).lower()}\n"
            )

    return StreamingResponse(_iter(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=sensor_readings.csv"})
