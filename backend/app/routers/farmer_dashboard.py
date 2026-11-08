"""Farmer-specific dashboard endpoints.

Provides aggregated statistics for the authenticated farmer.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import Farmer, Field, SensorReading, IrrigationSchedule, WeatherData
from app.schemas.farmer_dashboard import FarmerDashboardResponse
from app.routers.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/farmers/me", tags=["farmer_dashboard"])

@router.get("/dashboard", response_model=FarmerDashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    farmer_id: int = Depends(get_current_user),
):
    # Ensure farmer exists
    # Resolve farmer based on authenticated user
    # First get the User record
    user_record = db.query(User).filter(User.id == farmer_id).first()
    if not user_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # Assume Farmer is linked via email address
    farmer = db.query(Farmer).filter(Farmer.email == user_record.email).first()
    if not farmer:
        # Auto-create Farmer record if it doesn't exist yet for this user
        from uuid import uuid4
        farmer = Farmer(
            farmer_id=uuid4().hex[:32],
            name=user_record.full_name or "Farmer",
            email=user_record.email,
            is_demo=False,
        )
        db.add(farmer)
        db.commit()
        db.refresh(farmer)

    # Total fields
    total_fields = db.query(Field).filter(Field.farmer_id == farmer.farmer_id).count()

    # Fields needing irrigation (based on latest recommendation action)
    from app.services.irrigation_service import recommend_irrigation
    fields_needing = 0
    for field in db.query(Field).filter(Field.farmer_id == farmer.farmer_id).all():
        rec = recommend_irrigation(db=db, field_id=field.field_id)
        if rec.get("action") == "IRRIGATE_IMMEDIATELY":
            fields_needing += 1

    # Average soil moisture across recent sensor readings
    # Take the latest reading per field
    avg_moisture = None
    moisture_vals = []
    for field in db.query(Field).filter(Field.farmer_id == farmer.farmer_id).all():
        reading = (
            db.query(SensorReading)
            .filter(SensorReading.field_id == field.field_id)
            .order_by(SensorReading.timestamp.desc())
            .first()
        )
        if reading and reading.soil_moisture is not None:
            moisture_vals.append(reading.soil_moisture)
    if moisture_vals:
        avg_moisture = sum(moisture_vals) / len(moisture_vals)

    # Total water used from completed irrigation schedules
    total_water = (
        db.query(IrrigationSchedule)
        .join(Field, Field.field_id == IrrigationSchedule.field_id)
        .filter(Field.farmer_id == farmer.farmer_id)
        .filter(IrrigationSchedule.status == "completed")
        .with_entities(IrrigationSchedule.water_quantity_liters)
        .all()
    )
    total_water_used = sum([w[0] for w in total_water]) if total_water else 0.0

    # Latest weather summary (use most recent WeatherData across farmer's fields)
    latest_weather = (
        db.query(WeatherData)
        .join(Field, Field.field_id == WeatherData.field_id)
        .filter(Field.farmer_id == farmer.farmer_id)
        .order_by(WeatherData.timestamp.desc())
        .first()
    )
    weather_summary = None
    if latest_weather:
        weather_summary = {
            "temperature": latest_weather.temperature,
            "humidity": latest_weather.humidity,
            "rainfall": latest_weather.rainfall,
            "timestamp": latest_weather.timestamp,
        }

    return FarmerDashboardResponse(
        farmer_name=farmer.name or user_record.full_name,
        farmer_email=farmer.email or user_record.email,
        total_fields=total_fields,
        fields_needing_irrigation=fields_needing,
        average_soil_moisture=avg_moisture,
        total_water_used_liters=total_water_used,
        weather_summary=weather_summary,
    )
