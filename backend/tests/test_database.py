from datetime import datetime

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from app.models import Farmer, Field, Sensor, SensorReading, WeatherData

T = datetime(2026, 10, 7, 10, 30)


def make_chain(db):
    farmer = Farmer(farmer_id="FR001", name="Harini")
    field = Field(field_id="F001", farmer_id="FR001", name="North", crop_type="Rice", latitude=17.4, longitude=78.5)
    sensor = Sensor(sensor_id="SM001", field_id="F001")
    db.add_all([farmer, field, sensor])
    db.commit()
    return farmer, field, sensor


def test_relationship_chain_farmer_field_crop_sensor(db):
    farmer, field, sensor = make_chain(db)
    assert [f.field_id for f in farmer.fields] == ["F001"]
    assert field.farmer.name == "Harini" and field.crop_type == "Rice"
    assert [s.sensor_id for s in field.sensors] == ["SM001"]
    assert sensor.field.field_id == "F001"


def test_sensor_readings_persisted_and_linked(db):
    _, field, sensor = make_chain(db)
    db.add(SensorReading(sensor_id="SM001", field_id="F001", timestamp=T, soil_moisture=35.6, is_simulated=True))
    db.commit()
    db.expire_all()
    row = db.scalars(select(SensorReading)).one()
    assert row.reading_id is not None and row.soil_moisture == 35.6 and row.is_simulated is True
    assert row.sensor.sensor_id == "SM001" and row.field.field_id == "F001"
    assert len(field.sensor_readings) == 1 and len(sensor.readings) == 1


def test_weather_records_persisted_and_linked(db):
    _, field, _ = make_chain(db)
    db.add(WeatherData(field_id="F001", timestamp=T, temperature=29.0, humidity=68, rainfall=2.1))
    db.commit()
    db.expire_all()
    row = db.scalars(select(WeatherData)).one()
    assert (row.temperature, row.humidity, row.rainfall) == (29.0, 68, 2.1)
    assert row.field.farmer_id == "FR001" and len(field.weather_records) == 1


def test_foreign_keys_enforced(db):
    make_chain(db)
    db.add(SensorReading(sensor_id="NOPE", field_id="F001", timestamp=T, soil_moisture=10))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    db.add(Sensor(sensor_id="SM002", field_id="NOFIELD"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_unique_constraints_block_duplicates(db):
    make_chain(db)
    db.add(SensorReading(sensor_id="SM001", field_id="F001", timestamp=T, soil_moisture=10))
    db.commit()
    db.add(SensorReading(sensor_id="SM001", field_id="F001", timestamp=T, soil_moisture=11))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    db.add(WeatherData(field_id="F001", timestamp=T, temperature=1, humidity=1, rainfall=0))
    db.commit()
    db.add(WeatherData(field_id="F001", timestamp=T, temperature=2, humidity=2, rainfall=0))
    with pytest.raises(IntegrityError):
        db.commit()


def test_time_series_indexes_exist(engine):
    insp = inspect(engine)
    assert {"ix_reading_field_ts", "ix_reading_sensor_ts"} <= {i["name"] for i in insp.get_indexes("sensor_readings")}
    assert "ix_weather_field_ts" in {i["name"] for i in insp.get_indexes("weather_data")}
    assert insp.get_foreign_keys("sensors")[0]["referred_table"] == "fields"
    assert set(insp.get_table_names()) >= {"farmers", "fields", "sensors", "sensor_readings", "weather_data"}


def test_database_connection_and_masking(engine):
    from app.database.session import safe_database_url, verify_connection
    verify_connection(engine)
    masked = safe_database_url("postgresql+psycopg2://irrigation:supersecret@localhost:5433/irrigation")
    assert "supersecret" not in masked
    assert "***" in masked


def test_relational_schema_columns(engine):
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    assert {"farmers", "fields", "crops", "sensors", "sensor_readings", "weather_data"} <= tables

    farmer_cols = {c["name"] for c in insp.get_columns("farmers")}
    assert {"farmer_id", "name", "phone", "email", "created_at"} <= farmer_cols

    field_cols = {c["name"] for c in insp.get_columns("fields")}
    assert {"field_id", "farmer_id", "field_name", "location", "latitude", "longitude", "area_hectares", "created_at"} <= field_cols

    crop_cols = {c["name"] for c in insp.get_columns("crops")}
    assert {"crop_id", "field_id", "crop_type", "variety", "planting_date", "growth_stage"} <= crop_cols

    sensor_cols = {c["name"] for c in insp.get_columns("sensors")}
    assert {"sensor_id", "field_id", "measurement_type", "unit", "status", "connectivity_mode", "created_at"} <= sensor_cols

    reading_cols = {c["name"] for c in insp.get_columns("sensor_readings")}
    assert {"reading_id", "timestamp", "sensor_id", "field_id", "measurement_type", "value", "quality_status", "quality_flags", "is_simulated"} <= reading_cols

    weather_cols = {c["name"] for c in insp.get_columns("weather_data")}
    assert {"weather_id", "field_id", "timestamp", "temperature", "humidity", "rainfall", "wind_speed", "source"} <= weather_cols


def test_sensor_reading_insertion_and_quality(db):
    _, field, sensor = make_chain(db)
    reading = SensorReading(
        sensor_id=sensor.sensor_id,
        field_id=field.field_id,
        timestamp=T,
        soil_moisture=42.5,
        measurement_type="soil_moisture",
        value=42.5,
        unit="%",
        quality_status="valid",
        quality_flags="out_of_order",
        is_simulated=True,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    assert reading.reading_id is not None
    assert reading.quality_status == "valid"
    assert reading.quality_flags == "out_of_order"
    assert reading.is_simulated is True
    assert reading.measurement_type == "soil_moisture"


def test_historical_reading_retrieval_order(db):
    _, field, sensor = make_chain(db)
    from datetime import timedelta
    from app.services.sensor_service import list_readings

    t1 = T
    t2 = T + timedelta(hours=1)
    t3 = T + timedelta(hours=2)

    db.add_all([
        SensorReading(sensor_id=sensor.sensor_id, field_id=field.field_id, timestamp=t1, soil_moisture=30.0),
        SensorReading(sensor_id=sensor.sensor_id, field_id=field.field_id, timestamp=t2, soil_moisture=32.0),
        SensorReading(sensor_id=sensor.sensor_id, field_id=field.field_id, timestamp=t3, soil_moisture=34.0),
    ])
    db.commit()

    asc_readings = list_readings(db, sensor_id="SM001", field_id="F001", start=None, end=None, limit=10, order="asc")
    assert [r.timestamp for r in asc_readings] == [t1, t2, t3]

    desc_readings = list_readings(db, sensor_id="SM001", field_id="F001", start=None, end=None, limit=10, order="desc")
    assert [r.timestamp for r in desc_readings] == [t3, t2, t1]


def test_timescale_hypertable_status(engine):
    from app.database.timescale import hypertable_status, setup_timescale
    status = hypertable_status(engine)
    assert isinstance(status, dict)
    assert "available" in status
    assert "hypertables" in status
    res = setup_timescale(engine)
    assert isinstance(res, bool)


def test_persistence_across_restart(tmp_path):
    from app.database.init_db import init_db
    from app.database.session import build_engine
    from sqlalchemy.orm import sessionmaker

    db_path = tmp_path / "test_persist.db"
    url = f"sqlite:///{db_path}"

    eng1 = build_engine(url)
    init_db(eng1)
    sm1 = sessionmaker(bind=eng1)
    with sm1() as session1:
        farmer = Farmer(farmer_id="FR_P1", name="Persistent Farmer")
        field = Field(field_id="F_P1", farmer_id="FR_P1", name="Persist Field", crop_type="Wheat")
        sensor = Sensor(sensor_id="SM_P1", field_id="F_P1")
        reading = SensorReading(sensor_id="SM_P1", field_id="F_P1", timestamp=T, soil_moisture=25.0)
        session1.add_all([farmer, field, sensor, reading])
        session1.commit()
    eng1.dispose()

    eng2 = build_engine(url)
    init_db(eng2)
    sm2 = sessionmaker(bind=eng2)
    with sm2() as session2:
        r = session2.scalars(select(SensorReading).where(SensorReading.sensor_id == "SM_P1")).one()
        assert r.soil_moisture == 25.0
        assert r.sensor.field.farmer.name == "Persistent Farmer"
    eng2.dispose()
