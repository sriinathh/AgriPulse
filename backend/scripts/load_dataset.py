"""Load the generated SYNTHETIC dataset into the Week-1 database.

  python scripts/generate_dataset.py --out data/synthetic --raw
  python scripts/load_dataset.py --dir data/synthetic            # uses DATABASE_URL from .env

* farmers/fields/sensors go through the same registry service as the REST API
* every sensor reading passes the SAME cleaning functions as live ingestion
  (so injected nulls / impossible values are rejected and counted, never stored)
* weather is NOT loaded: the weather_data table holds live OpenWeatherMap data only
* irrigation_events.csv / irrigation_dataset.csv are for Week 3 and are not loaded (no table exists yet)
"""
import argparse
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.init_db import init_db  # noqa: E402
from app.database.session import get_engine, get_sessionmaker  # noqa: E402
from app.models import SensorReading  # noqa: E402
from app.schemas.farmer import FarmerCreate  # noqa: E402
from app.models import Farmer, Field  # noqa: E402
from app.schemas.field import FieldCreate  # noqa: E402
from app.schemas.sensor import SensorCreate  # noqa: E402
from app.services import registry_service as registry  # noqa: E402
from app.services.data_cleaning_service import DataValidationError, clean_sensor_reading  # noqa: E402

CHUNK = 5000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="data/synthetic")
    a = ap.parse_args()
    d = Path(a.dir)
    init_db(get_engine())
    db = get_sessionmaker()()

    fields = pd.read_csv(d / "fields.csv")
    for _, r in fields.drop_duplicates("farmer_id").iterrows():
        if db.get(Farmer, r.farmer_id) is None:
            registry.create_farmer(db, FarmerCreate(farmer_id=r.farmer_id, name=r.farmer_name))
    for _, r in fields.iterrows():
        if db.get(Field, r.field_id) is None:
            registry.create_field(db, FieldCreate(
                field_id=r.field_id, farmer_id=r.farmer_id, name=r["name"], location_name=r.location_name,
                latitude=r.latitude, longitude=r.longitude, crop_type=r.crop_type, area_hectares=r.area_hectares))
            registry.create_sensor(db, SensorCreate(sensor_id=r.sensor_id, field_id=r.field_id))
    print(f"registered {len(fields)} fields/sensors")

    stored, rejected, batch = 0, Counter(), []
    for r in pd.read_csv(d / "sensor_readings.csv").itertuples(index=False):
        sm = None if pd.isna(r.soil_moisture) else r.soil_moisture
        try:
            c = clean_sensor_reading(sm, r.timestamp)
        except DataValidationError as e:
            rejected.update(f"{i.field}:{i.code}" for i in e.issues)
            continue
        batch.append(SensorReading(sensor_id=r.sensor_id, field_id=r.field_id, timestamp=c.timestamp,
                                   soil_moisture=c.soil_moisture, is_simulated=bool(r.is_simulated)))
        if len(batch) >= CHUNK:
            db.add_all(batch); db.commit(); stored += len(batch); batch = []
    db.add_all(batch); db.commit(); stored += len(batch)
    print(f"sensor readings: stored {stored}, rejected {sum(rejected.values())} {dict(rejected)}")
    print("weather_data table untouched: it is filled only by live API calls (GET /weather/{field_id}).")

if __name__ == "__main__":
    main()
