from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import Field
from app.schemas.combined import CombinedFieldData
from app.schemas.field import CropUpdate, FieldCreate, FieldDetail, FieldOut, FieldUpdate
from app.schemas.sensor import SensorOut
from app.services import combined_service, registry_service as registry

router = APIRouter(prefix="/fields", tags=["fields"])


@router.post("", response_model=FieldOut, status_code=201)
def create_field(body: FieldCreate, db: Session = Depends(get_db)):
    return registry.create_field(db, body)


@router.get("", response_model=List[FieldOut])
def list_fields(farmer_id: Optional[str] = None, db: Session = Depends(get_db)):
    stmt = select(Field).order_by(Field.field_id)
    if farmer_id:
        stmt = stmt.where(Field.farmer_id == farmer_id)
    return db.scalars(stmt).all()


@router.get("/{field_id}", response_model=FieldDetail)
def get_field(field_id: str, db: Session = Depends(get_db)):
    return registry.get_field_or_404(db, field_id)


@router.put("/{field_id}", response_model=FieldOut)
def update_field(field_id: str, body: FieldUpdate, db: Session = Depends(get_db)):
    return registry.update_field(db, field_id, body)


@router.delete("/{field_id}", status_code=204)
def delete_field(field_id: str, db: Session = Depends(get_db)):
    registry.delete_field(db, field_id)


@router.put("/{field_id}/crop", response_model=FieldOut)
def assign_crop(field_id: str, body: CropUpdate, db: Session = Depends(get_db)):
    return registry.update_crop(db, field_id, body.crop_type)


@router.get("/{field_id}/sensors", response_model=List[SensorOut])
def field_sensors(field_id: str, db: Session = Depends(get_db)):
    return registry.get_field_or_404(db, field_id).sensors


@router.get("/{field_id}/combined", response_model=CombinedFieldData)
def combined(field_id: str, limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    """Field + sensors + recent soil-moisture readings, each paired with the latest weather at/before it."""
    return combined_service.combined_field_data(db, field_id, limit)
