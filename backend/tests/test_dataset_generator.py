import subprocess
import sys
from pathlib import Path

import pandas as pd

from app.services.data_cleaning_service import DataValidationError, clean_sensor_reading

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "generate_dataset.py"


def run(out, seed=1):
    subprocess.run([sys.executable, str(SCRIPT), "--out", str(out), "--raw", "--fields", "4", "--days", "40", "--seed", str(seed)],
                   check=True, capture_output=True)


def test_generator_is_deterministic_and_matches_week1_contracts(tmp_path):
    run(tmp_path / "a")
    run(tmp_path / "b")
    for name in ("sensor_readings", "irrigation_dataset", "irrigation_events", "fields"):
        assert (tmp_path / "a" / f"{name}.csv").read_bytes() == (tmp_path / "b" / f"{name}.csv").read_bytes()
    s = pd.read_csv(tmp_path / "a" / "sensor_readings.csv")
    assert list(s.columns) == ["sensor_id", "field_id", "timestamp", "soil_moisture", "is_simulated"]
    assert s.is_simulated.all()
    assert not (tmp_path / "a" / "weather_data.csv").exists()  # weather must come from the live API only


def test_every_injected_fault_is_caught_by_the_cleaning_layer(tmp_path):
    run(tmp_path)
    s = pd.read_csv(tmp_path / "sensor_readings.csv")
    rejected = accepted_bad = 0
    for v, ts in zip(s.soil_moisture, s.timestamp):
        try:
            c = clean_sensor_reading(None if pd.isna(v) else v, ts)
            if not 0 <= c.soil_moisture <= 100:
                accepted_bad += 1
        except DataValidationError:
            rejected += 1
    assert rejected > 0 and accepted_bad == 0  # faults exist, and none slip through


def test_dataset_has_both_targets_and_sensor_and_weather_features(tmp_path):
    run(tmp_path)
    m = pd.read_csv(tmp_path / "irrigation_dataset.csv")
    assert {"irrigate_today", "irrigation_mm", "growth_stage", "soil_moisture_0600", "temperature_0600", "humidity_0600", "rain_forecast_next24h_mm"} <= set(m.columns)
    assert ((m.irrigate_today == 0) == (m.irrigation_mm == 0)).all()
