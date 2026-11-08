"""Development-only demo dataset. Records are labelled is_demo / is_simulated / is_mock."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.errors import AppError
from app.models import Crop, Farmer
from app.schemas.crop import CropPatch
from app.schemas.farmer import FarmerCreate
from app.schemas.field import FieldCreate
from app.schemas.sensor import SensorCreate
from app.schemas.sensor_reading import SensorReadingIn
from app.services import registry_service as registry
from app.services import sensor_service, weather_service
from app.services.weather_service import ProviderWeather

DEMO_FARMER = "FRDEMO"


def seed_demo(db: Session, settings: Settings) -> dict:
    if settings.is_production:
        raise AppError(403, "demo_disabled", "Demo data cannot be seeded when APP_ENV=production.")
    existing = db.get(Farmer, DEMO_FARMER)
    if existing is not None:
        return {"status": "already_seeded", "farmer_id": DEMO_FARMER, "created": False}

    registry.create_farmer(
        db, FarmerCreate(farmer_id=DEMO_FARMER, name="Demo Farmer (simulated)", phone="0000000000"), is_demo=True
    )
    north = registry.create_field(db, FieldCreate(
        field_id="FDEMO1", farmer_id=DEMO_FARMER, name="Demo North Field",
        location_name="Hyderabad, Telangana", latitude=17.385, longitude=78.4867,
        crop_type="Rice", area_hectares=1.2,
    ), is_demo=True)
    south = registry.create_field(db, FieldCreate(
        field_id="FDEMO2", farmer_id=DEMO_FARMER, name="Demo South Field",
        location_name="Hyderabad, Telangana", latitude=17.4, longitude=78.5,
        crop_type="Maize", area_hectares=0.8,
    ), is_demo=True)

    for crop in db.scalars(select(Crop).where(Crop.field_id.in_(["FDEMO1", "FDEMO2"]))).all():
        registry.update_crop_record(db, crop.crop_id, CropPatch(variety="Demo variety", growth_stage="vegetative"))

    sm = registry.create_sensor(db, SensorCreate(sensor_id="SMDEMO1", field_id=north.field_id, is_simulated=True), is_demo=True)
    th = registry.create_sensor(
        db,
        SensorCreate(sensor_id="SMDEMO2", field_id=south.field_id, sensor_type="temperature", is_simulated=True),
        is_demo=True,
    )

    now = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    for i in range(12):
        ts = (now - timedelta(hours=11 - i)).isoformat()
        sensor_service.ingest_reading(
            db,
            SensorReadingIn(sensor_id=sm.sensor_id, timestamp=ts, soil_moisture=round(34 + i * 0.4, 2), is_simulated=True),
            settings,
            source="demo",
        )
        sensor_service.ingest_reading(
            db,
            SensorReadingIn(
                sensor_id=th.sensor_id, timestamp=ts, measurement_type="temperature",
                value=round(26 + (i % 5) * 0.6, 2), is_simulated=True,
            ),
            settings,
            source="demo",
        )

    mock = ProviderWeather(now, 29.4, 61.0, 0.0, description="simulated haze (mock)", wind_speed=2.1)
    weather_service.store_weather(db, north.field_id, mock, source="mock", is_mock=True)
    weather_service.store_weather(db, south.field_id, mock, source="mock", is_mock=True)

    # Seed initial demo irrigation schedules
    from app.models.irrigation_schedule import IrrigationSchedule, ScheduleStatus
    db.add_all([
        IrrigationSchedule(
            schedule_id="SCH_DEMO_01",
            field_id=north.field_id,
            recommended_date=now,
            recommended_time="06:30",
            duration_minutes=45.0,
            water_quantity_liters=1200.0,
            priority="high",
            reason="Low soil moisture (34%) detected below 45% threshold for Rice",
            status=ScheduleStatus.pending,
        ),
        IrrigationSchedule(
            schedule_id="SCH_DEMO_02",
            field_id=south.field_id,
            recommended_date=now - timedelta(days=1),
            recommended_time="17:00",
            duration_minutes=30.0,
            water_quantity_liters=800.0,
            priority="medium",
            reason="Routine vegetative maintenance watering",
            status=ScheduleStatus.completed,
        ),
    ])
    db.commit()

    return {
        "status": "seeded",
        "created": True,
        "farmer_id": DEMO_FARMER,
        "fields": [north.field_id, south.field_id],
        "sensors": [sm.sensor_id, th.sensor_id],
        "label": "All demo records are labelled is_demo / is_simulated / is_mock. They are not hardware or live weather.",
    }
