from datetime import datetime

import pytest

from app.services.data_cleaning_service import (
    DataValidationError, clean_sensor_reading, clean_weather,
)

NOW = datetime(2026, 10, 7, 12, 0, 0)


def codes(exc):
    return {(i.field, i.code) for i in exc.value.issues}


def test_valid_reading_passes():
    r = clean_sensor_reading(35.6, "2026-10-07T10:30:00", now=NOW)
    assert r.soil_moisture == 35.6 and r.timestamp == datetime(2026, 10, 7, 10, 30) and r.timestamp_source == "client"


def test_missing_moisture_rejected():
    for bad in (None, "", "   "):
        with pytest.raises(DataValidationError) as e:
            clean_sensor_reading(bad, "2026-10-07T10:30:00", now=NOW)
        assert codes(e) == {("soil_moisture", "missing_value")}


@pytest.mark.parametrize("bad,code", [(-1, "out_of_range"), (100.5, "out_of_range"), (1000, "out_of_range"),
                                      ("abc", "not_numeric"), (True, "not_numeric"),
                                      (float("nan"), "not_finite"), (float("inf"), "not_finite")])
def test_invalid_moisture_rejected(bad, code):
    with pytest.raises(DataValidationError) as e:
        clean_sensor_reading(bad, "2026-10-07T10:30:00", now=NOW)
    assert codes(e) == {("soil_moisture", code)}


def test_boundaries_accepted():
    assert clean_sensor_reading(0, None, now=NOW).soil_moisture == 0
    assert clean_sensor_reading(100, None, now=NOW).soil_moisture == 100


def test_numeric_string_and_rounding_are_cleaned_and_noted():
    r = clean_sensor_reading(" 35.678 ", "2026-10-07T10:30:00", now=NOW)
    assert r.soil_moisture == 35.68
    assert any("rounded" in n for n in r.notes) and any("string" in n for n in r.notes)


def test_missing_timestamp_uses_server_time_and_is_flagged():
    r = clean_sensor_reading(40, None, now=NOW)
    assert r.timestamp == NOW and r.timestamp_source == "server"
    assert any("timestamp missing" in n for n in r.notes)


def test_timezone_aware_timestamp_converted_to_utc():
    r = clean_sensor_reading(40, "2026-10-07T16:00:00+05:30", now=NOW)
    assert r.timestamp == datetime(2026, 10, 7, 10, 30)
    assert clean_sensor_reading(40, "2026-10-07T10:30:00Z", now=NOW).timestamp == datetime(2026, 10, 7, 10, 30)


@pytest.mark.parametrize("bad,code", [("yesterday", "invalid_timestamp"), (12345, "invalid_timestamp"),
                                      ("2026-10-08T10:30:00", "future_timestamp")])
def test_bad_timestamp_rejected(bad, code):
    with pytest.raises(DataValidationError) as e:
        clean_sensor_reading(40, bad, now=NOW)
    assert codes(e) == {("timestamp", code)}


def test_all_issues_reported_together():
    with pytest.raises(DataValidationError) as e:
        clean_sensor_reading(None, "garbage", now=NOW)
    assert codes(e) == {("soil_moisture", "missing_value"), ("timestamp", "invalid_timestamp")}


def test_weather_clean_ok_and_rejects_implausible_or_missing():
    w = clean_weather(29.0, 68, 2.1)
    assert (w.temperature, w.humidity, w.rainfall) == (29.0, 68.0, 2.1)
    with pytest.raises(DataValidationError) as e:
        clean_weather(200, 150, -3)
    assert {i.field for i in e.value.issues} == {"temperature", "humidity", "rainfall"}
    with pytest.raises(DataValidationError):
        clean_weather(None, 50, 0)
