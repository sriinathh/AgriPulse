"""Irrigation schedule management endpoints."""
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import Field, IrrigationSchedule
from app.schemas.irrigation_schedule import (
    IrrigationScheduleCreate,
    IrrigationScheduleOut,
    IrrigationScheduleStatusUpdate,
    ScheduleStatus,
)
from app.services.irrigation_service import recommend_irrigation

router = APIRouter(prefix="/irrigation/schedules", tags=["irrigation_schedules"])


@router.get("", response_model=List[IrrigationScheduleOut])
def list_schedules(
    field_id: Optional[str] = None,
    status_filter: Optional[ScheduleStatus] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Retrieve irrigation schedules with optional field or status filtering."""
    stmt = select(IrrigationSchedule)
    if field_id:
        stmt = stmt.where(IrrigationSchedule.field_id == field_id)
    if status_filter:
        stmt = stmt.where(IrrigationSchedule.status == status_filter)
    stmt = stmt.order_by(desc(IrrigationSchedule.recommended_date), desc(IrrigationSchedule.created_at)).limit(limit)
    return db.scalars(stmt).all()


@router.post("", response_model=IrrigationScheduleOut, status_code=status.HTTP_201_CREATED)
def create_schedule(payload: IrrigationScheduleCreate, db: Session = Depends(get_db)):
    """Manually or rule-based create an irrigation schedule."""
    # Ensure field exists
    field = db.get(Field, payload.field_id)
    if not field:
        raise HTTPException(status_code=404, detail=f"Field '{payload.field_id}' does not exist.")

    sched = IrrigationSchedule(
        schedule_id=f"SCH_{uuid.uuid4().hex[:12].upper()}",
        field_id=payload.field_id,
        recommended_date=payload.recommended_date,
        recommended_time=payload.recommended_time,
        duration_minutes=payload.duration_minutes,
        water_quantity_liters=payload.water_quantity_liters,
        priority=payload.priority or "normal",
        reason=payload.reason or "Scheduled irrigation recommendation",
        status=ScheduleStatus.pending,
    )
    db.add(sched)
    db.commit()
    db.refresh(sched)
    return sched


@router.post("/generate/{field_id}", response_model=IrrigationScheduleOut, status_code=status.HTTP_201_CREATED)
def generate_schedule_for_field(field_id: str, db: Session = Depends(get_db)):
    """Generate and persist an irrigation schedule based on latest FAO-56 agro recommendations."""
    field = db.get(Field, field_id)
    if not field:
        raise HTTPException(status_code=404, detail=f"Field '{field_id}' does not exist.")

    rec = recommend_irrigation(db=db, field_id=field_id)
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Determine liters: area_hectares * recommended_water_mm * 10,000 L/ha-mm
    hectares = field.area_hectares or 1.0
    rec_mm = rec.get("recommended_water_mm", 10.0)
    water_liters = max(100.0, round(hectares * rec_mm * 100.0, 1))
    duration_mins = max(15.0, round((water_liters / 50.0), 1))  # Approx pump rate

    priority_map = {
        "IRRIGATE_IMMEDIATELY": "high",
        "IRRIGATE_LIGHT": "medium",
        "MAINTAIN_MONITORING": "low",
        "DEFER_DUE_TO_RAIN": "low",
    }
    action = rec.get("action", "MAINTAIN_MONITORING")

    sched = IrrigationSchedule(
        schedule_id=f"SCH_{uuid.uuid4().hex[:12].upper()}",
        field_id=field_id,
        recommended_date=now,
        recommended_time=now.strftime("%H:%M"),
        duration_minutes=duration_mins,
        water_quantity_liters=water_liters,
        priority=priority_map.get(action, "normal"),
        reason=rec.get("reason", "FAO-56 Irrigation Recommendation"),
        status=ScheduleStatus.pending,
    )
    db.add(sched)
    db.commit()
    db.refresh(sched)
    return sched


@router.patch("/{schedule_id}/status", response_model=IrrigationScheduleOut)
def update_schedule_status(
    schedule_id: str,
    update: IrrigationScheduleStatusUpdate,
    db: Session = Depends(get_db),
):
    """Update status of a schedule (e.g. pending -> completed or skipped)."""
    sched = db.get(IrrigationSchedule, schedule_id)
    if not sched:
        raise HTTPException(status_code=404, detail=f"Schedule '{schedule_id}' does not exist.")

    sched.status = update.status
    sched.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(sched)
    db.commit()
    db.refresh(sched)
    return sched

