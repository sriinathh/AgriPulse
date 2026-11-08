"""Verification script for Sensor reading insertion, chronological retrieval, and restart persistence."""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.session import build_engine, get_engine
from app.models import Farmer, Field, Sensor, SensorReading
from app.services.sensor_service import list_readings
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

def main():
    engine = get_engine()
    sm = sessionmaker(bind=engine)
    ts = datetime(2026, 10, 14, 21, 0, 0)

    print("=== Testing Sensor Reading Ingestion & Historical Persistence in TimescaleDB ===")
    with sm() as db:
        # Ensure verification farmer/field/sensor exist
        farmer = db.get(Farmer, "FR_VERIFY_1")
        if not farmer:
            farmer = Farmer(farmer_id="FR_VERIFY_1", name="Verification Farmer", phone="1234567890", email="verify@example.com")
            db.add(farmer)
            db.flush()

        field = db.get(Field, "F_VERIFY_1")
        if not field:
            field = Field(
                field_id="F_VERIFY_1",
                farmer_id="FR_VERIFY_1",
                name="Verification Field",
                field_name="Verification Field",
                location="Hyderabad, Telangana",
                location_name="Hyderabad, Telangana",
                crop_type="Wheat",
                area_hectares=2.5,
            )
            db.add(field)
            db.flush()

        sensor = db.get(Sensor, "SM_VERIFY_1")
        if not sensor:
            sensor = Sensor(
                sensor_id="SM_VERIFY_1",
                field_id="F_VERIFY_1",
                sensor_type="soil_moisture",
                measurement_type="soil_moisture",
                unit="%",
                status="active",
                connectivity_mode="cellular",
                is_simulated=True,
            )
            db.add(sensor)
            db.flush()

        # Insert test reading
        existing_reading = db.scalar(
            select(SensorReading).where(SensorReading.sensor_id == "SM_VERIFY_1", SensorReading.timestamp == ts)
        )
        if not existing_reading:
            reading = SensorReading(
                sensor_id="SM_VERIFY_1",
                field_id="F_VERIFY_1",
                timestamp=ts,
                soil_moisture=38.5,
                measurement_type="soil_moisture",
                value=38.5,
                unit="%",
                quality_status="valid",
                quality_flags=None,
                is_simulated=True,
            )
            db.add(reading)
        db.commit()

        # Retrieve chronological order
        readings_asc = list_readings(db, sensor_id="SM_VERIFY_1", field_id="F_VERIFY_1", start=None, end=None, limit=5, order="asc")
        readings_desc = list_readings(db, sensor_id="SM_VERIFY_1", field_id="F_VERIFY_1", start=None, end=None, limit=5, order="desc")
        print(f"Readings count (SM_VERIFY_1): {len(readings_asc)}")
        print(f"Earliest reading (ASC): {readings_asc[0].timestamp} -> {readings_asc[0].soil_moisture}%")
        print(f"Latest reading (DESC): {readings_desc[0].timestamp} -> {readings_desc[0].soil_moisture}%")

    # Simulate application restart: dispose engine and open fresh engine
    print("\n=== Simulating Backend Restart & Verifying Historical Persistence ===")
    from app.config import get_settings
    engine.dispose()

    engine2 = build_engine(get_settings().database_url)
    sm2 = sessionmaker(bind=engine2)
    with sm2() as db2:
        persisted = db2.scalar(
            select(SensorReading).where(SensorReading.sensor_id == "SM_VERIFY_1", SensorReading.timestamp == ts)
        )
        assert persisted is not None, "Reading did not persist after restart!"
        assert persisted.soil_moisture == 38.5, f"Value mismatch: {persisted.soil_moisture}"
        assert persisted.sensor.field.field_name == "Verification Field"
        print(f"Reading successfully verified from TimescaleDB hypertable after engine restart!")
        print(f"  - Reading ID: {persisted.reading_id}")
        print(f"  - Timestamp: {persisted.timestamp}")
        print(f"  - Soil Moisture: {persisted.soil_moisture}%")
        print(f"  - Quality Status: {persisted.quality_status}")
        print(f"  - Linked Field Name: {persisted.field.field_name}")
        print(f"  - Linked Farmer: {persisted.field.farmer.name}")

    engine2.dispose()
    print("\nAll historical sensor data verification tests passed successfully!")

if __name__ == "__main__":
    main()
