from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.crop import CropCreate, CropOut, CropPatch
from app.services import registry_service as registry

router = APIRouter(prefix="/crops", tags=["crops"])


@router.post("", response_model=CropOut, status_code=201)
def create_crop(body: CropCreate, db: Session = Depends(get_db)):
    return registry.create_crop(db, body)


@router.get("", response_model=List[CropOut])
def list_crops(field_id: Optional[str] = None, db: Session = Depends(get_db)):
    return registry.list_crops(db, field_id)


@router.get("/{crop_id}", response_model=CropOut)
def get_crop(crop_id: str, db: Session = Depends(get_db)):
    return registry.get_crop_or_404(db, crop_id)


@router.put("/{crop_id}", response_model=CropOut)
def update_crop(crop_id: str, body: CropPatch, db: Session = Depends(get_db)):
    return registry.update_crop_record(db, crop_id, body)


@router.delete("/{crop_id}", status_code=204)
def delete_crop(crop_id: str, db: Session = Depends(get_db)):
    registry.delete_crop(db, crop_id)
