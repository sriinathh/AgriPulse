"""Farmer / field / sensor / crop registration. No HTTP or external-API code in here."""
from typing import Optional, Type

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import AppError
from app.models import Crop, Farmer, Field, Sensor, SensorReading, WeatherData
from app.models.farmer import utcnow
from app.schemas.crop import CropCreate, CropPatch
from app.schemas.farmer import FarmerCreate, FarmerUpdate
from app.schemas.field import FieldCreate, FieldUpdate
from app.schemas.sensor import SensorCreate, SensorUpdate
from app.services.data_cleaning_service import DEFAULT_UNITS


def _next_id(db: Session, model: Type, pk_name: str, prefix: str) -> str:
    n = db.scalar(select(func.count()).select_from(model)) or 0
    while True:
        n += 1
        candidate = f"{prefix}{n:03d}"
        if db.get(model, candidate) is None:
            return candidate


def _insert(db: Session, obj, label: str, obj_id: str):
    db.add(obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "duplicate_id", f"{label} '{obj_id}' already exists.")
    return obj


def get_farmer_or_404(db: Session, farmer_id: str) -> Farmer:
    farmer = db.get(Farmer, farmer_id)
    if farmer is None:
        raise AppError(404, "farmer_not_found", f"Farmer '{farmer_id}' does not exist.")
    return farmer


def get_field_or_404(db: Session, field_id: str) -> Field:
    field = db.get(Field, field_id)
    if field is None:
        raise AppError(404, "field_not_found", f"Field '{field_id}' does not exist.")
    return field


def get_sensor_or_404(db: Session, sensor_id: str) -> Sensor:
    sensor = db.get(Sensor, sensor_id)
    if sensor is None:
        raise AppError(404, "sensor_not_found", f"Sensor '{sensor_id}' is not registered.")
    return sensor


def get_crop_or_404(db: Session, crop_id: str) -> Crop:
    crop = db.get(Crop, crop_id)
    if crop is None:
        raise AppError(404, "crop_not_found", f"Crop '{crop_id}' does not exist.")
    return crop


def create_farmer(db: Session, data: FarmerCreate, is_demo: bool = False) -> Farmer:
    farmer_id = data.farmer_id or _next_id(db, Farmer, "farmer_id", "FR")
    farmer = Farmer(
        farmer_id=farmer_id, name=data.name.strip(), phone=data.phone, email=data.email, is_demo=is_demo
    )
    return _insert(db, farmer, "Farmer", farmer_id)


def update_farmer(db: Session, farmer_id: str, data: FarmerUpdate) -> Farmer:
    farmer = get_farmer_or_404(db, farmer_id)
    payload = data.model_dump(exclude_unset=True)
    for key, value in payload.items():
        if key == "name" and isinstance(value, str):
            value = value.strip()
        setattr(farmer, key, value)
    farmer.updated_at = utcnow()
    db.commit()
    return farmer


def delete_farmer(db: Session, farmer_id: str) -> None:
    farmer = get_farmer_or_404(db, farmer_id)
    for field in list(farmer.fields):
        delete_field(db, field.field_id, _commit=False)
    db.delete(farmer)
    db.commit()


def create_field(db: Session, data: FieldCreate, is_demo: bool = False) -> Field:
    get_farmer_or_404(db, data.farmer_id)
    field_id = data.field_id or _next_id(db, Field, "field_id", "F")
    dumped = data.model_dump(exclude={"field_id"})
    field = Field(field_id=field_id, is_demo=is_demo, **dumped)
    field = _insert(db, field, "Field", field_id)
    crop = Crop(
        crop_id=_next_id(db, Crop, "crop_id", "CR"),
        field_id=field.field_id,
        crop_type=field.crop_type,
        is_demo=is_demo,
    )
    db.add(crop)
    db.commit()
    return field


def update_field(db: Session, field_id: str, data: FieldUpdate) -> Field:
    field = get_field_or_404(db, field_id)
    payload = data.model_dump(exclude_unset=True)
    if "farmer_id" in payload:
        get_farmer_or_404(db, payload["farmer_id"])
    for key, value in payload.items():
        setattr(field, key, value)
    field.updated_at = utcnow()
    db.commit()
    return field


def delete_field(db: Session, field_id: str, _commit: bool = True) -> None:
    field = get_field_or_404(db, field_id)
    db.query(SensorReading).filter(SensorReading.field_id == field_id).delete()
    db.query(WeatherData).filter(WeatherData.field_id == field_id).delete()
    db.query(Crop).filter(Crop.field_id == field_id).delete()
    db.query(Sensor).filter(Sensor.field_id == field_id).delete()
    db.delete(field)
    if _commit:
        db.commit()


def update_crop(db: Session, field_id: str, crop_type: str) -> Field:
    field = get_field_or_404(db, field_id)
    field.crop_type = crop_type
    field.updated_at = utcnow()
    db.commit()
    return field


def create_crop(db: Session, data: CropCreate, is_demo: bool = False) -> Crop:
    field = get_field_or_404(db, data.field_id)
    crop_id = data.crop_id or _next_id(db, Crop, "crop_id", "CR")
    crop = Crop(
        crop_id=crop_id,
        field_id=data.field_id,
        crop_type=data.crop_type,
        variety=data.variety,
        planting_date=data.planting_date,
        growth_stage=data.growth_stage,
        notes=data.notes,
        is_demo=is_demo,
    )
    crop = _insert(db, crop, "Crop", crop_id)
    field.crop_type = data.crop_type
    field.updated_at = utcnow()
    db.commit()
    return crop


def update_crop_record(db: Session, crop_id: str, data: CropPatch) -> Crop:
    crop = get_crop_or_404(db, crop_id)
    payload = data.model_dump(exclude_unset=True)
    if "field_id" in payload:
        get_field_or_404(db, payload["field_id"])
    for key, value in payload.items():
        setattr(crop, key, value)
    crop.updated_at = utcnow()
    if "crop_type" in payload:
        field = get_field_or_404(db, crop.field_id)
        field.crop_type = payload["crop_type"]
        field.updated_at = utcnow()
    db.commit()
    return crop


def delete_crop(db: Session, crop_id: str) -> None:
    crop = get_crop_or_404(db, crop_id)
    db.delete(crop)
    db.commit()


def create_sensor(db: Session, data: SensorCreate, is_demo: bool = False) -> Sensor:
    get_field_or_404(db, data.field_id)
    sensor_id = data.sensor_id or _next_id(db, Sensor, "sensor_id", "SM")
    sensor = Sensor(
        sensor_id=sensor_id,
        field_id=data.field_id,
        sensor_type=data.sensor_type or "soil_moisture",
        measurement_type=data.measurement_type or data.sensor_type or "soil_moisture",
        status=data.status,
        unit=data.unit or DEFAULT_UNITS.get(data.sensor_type),
        connectivity_mode=data.connectivity_mode or "cellular",
        is_simulated=data.is_simulated,
        is_demo=is_demo,
    )
    return _insert(db, sensor, "Sensor", sensor_id)


def update_sensor(db: Session, sensor_id: str, data: SensorUpdate) -> Sensor:
    sensor = get_sensor_or_404(db, sensor_id)
    payload = data.model_dump(exclude_unset=True)
    if "field_id" in payload:
        get_field_or_404(db, payload["field_id"])
    for key, value in payload.items():
        setattr(sensor, key, value)
    sensor.updated_at = utcnow()
    db.commit()
    return sensor


def delete_sensor(db: Session, sensor_id: str) -> None:
    sensor = get_sensor_or_404(db, sensor_id)
    db.query(SensorReading).filter(SensorReading.sensor_id == sensor_id).delete()
    db.delete(sensor)
    db.commit()


def set_sensor_status(db: Session, sensor_id: str, status: str) -> Sensor:
    sensor = get_sensor_or_404(db, sensor_id)
    sensor.status = status
    sensor.updated_at = utcnow()
    db.commit()
    return sensor


def list_crops(db: Session, field_id: Optional[str] = None):
    stmt = select(Crop).order_by(Crop.crop_id)
    if field_id:
        stmt = stmt.where(Crop.field_id == field_id)
    return list(db.scalars(stmt))
