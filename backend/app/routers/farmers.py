from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import Farmer
from app.schemas.farmer import FarmerCreate, FarmerOut, FarmerUpdate
from app.schemas.field import FarmerDetail
from app.services import registry_service as registry

router = APIRouter(prefix="/farmers", tags=["farmers"])


@router.post("", response_model=FarmerOut, status_code=201)
def create_farmer(body: FarmerCreate, db: Session = Depends(get_db)):
    return registry.create_farmer(db, body)


@router.get("", response_model=List[FarmerOut])
def list_farmers(db: Session = Depends(get_db)):
    return db.scalars(select(Farmer).order_by(Farmer.farmer_id)).all()


@router.get("/{farmer_id}", response_model=FarmerDetail)
def get_farmer(farmer_id: str, db: Session = Depends(get_db)):
    return registry.get_farmer_or_404(db, farmer_id)


@router.put("/{farmer_id}", response_model=FarmerOut)
def update_farmer(farmer_id: str, body: FarmerUpdate, db: Session = Depends(get_db)):
    return registry.update_farmer(db, farmer_id, body)


@router.delete("/{farmer_id}", status_code=204)
def delete_farmer(farmer_id: str, db: Session = Depends(get_db)):
    registry.delete_farmer(db, farmer_id)
