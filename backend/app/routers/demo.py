from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database.session import get_db
from app.services import demo_service

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/seed")
def seed_demo(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return demo_service.seed_demo(db, settings)
