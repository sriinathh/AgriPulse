from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import DataQualityEvent
from app.services import quality_service

router = APIRouter(prefix="/data-quality", tags=["data-quality"])


class QualityEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    event_id: int
    event_type: str
    source: str
    sensor_id: Optional[str]
    field_id: Optional[str]
    message: str
    details: Optional[str]
    created_at: object


@router.get("/stats")
def quality_stats(db: Session = Depends(get_db)):
    return quality_service.stats(db)


@router.get("/events", response_model=List[QualityEventOut])
def quality_events(
    limit: int = Query(100, ge=1, le=500),
    event_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return quality_service.list_events(db, limit, event_type)
