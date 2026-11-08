import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

valid_payload = {
    "days_after_sowing": 30,
    "soil_moisture_0600": 20.5,
    "soil_moisture_change_24h": 1.2,
    "temperature_0600": 25.0,
    "humidity_0600": 55.0,
    "rain_prev24h_mm": 0.0,
    "rain_forecast_next24h_mm": 0.0,
    "irrigation_prev7d_mm": 0.0,
    "days_since_irrigation": 5,
    "crop_type": "wheat",
    "soil_type": "loam",
    "irrigation_type": "drip",
    "growth_stage": "vegetative"
}

@pytest.mark.parametrize(
    "field, value, expected_error",
    [
        ("humidity_0600", 150, "ensure this value is less than or equal to 100"),
        ("days_after_sowing", -5, "ensure this value is greater than or equal to 0"),
        ("soil_moisture_0600", "nan", "value is not a valid float"),
        ("crop_type", "unknown_crop", "unexpected value; permitted: ")
    ],
)
def test_invalid_inputs(field, value, expected_error):
    payload = valid_payload.copy()
    payload[field] = value
    response = client.post("/irrigation/predict", json=payload)
    assert response.status_code == 422
    assert expected_error in response.text

def test_missing_payload_field():
    payload = valid_payload.copy()
    payload.pop("temperature_0600")
    response = client.post("/irrigation/predict", json=payload)
    assert response.status_code == 422
    assert "field required" in response.text
