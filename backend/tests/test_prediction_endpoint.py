import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Load a valid payload template from the training data columns
valid_payload = {
    "days_after_sowing": 30,
    "soil_moisture_0600": 12.5,
    "soil_moisture_change_24h": 0.3,
    "temperature_0600": 22.0,
    "humidity_0600": 55.0,
    "rain_prev24h_mm": 0.0,
    "rain_forecast_next24h_mm": 0.0,
    "irrigation_prev7d_mm": 5.0,
    "days_since_irrigation": 2,
    "crop_type": "wheat",
    "soil_type": "loam",
    "irrigation_type": "drip",
    "growth_stage": "vegetative"
}

def test_predict_success():
    response = client.post("/irrigation/predict", json=valid_payload)
    assert response.status_code == 200
    data = response.json()
    assert "irrigation_mm" in data
    assert isinstance(data["irrigation_mm"], (float, int))
    assert data["model_name"] == "irrigation_model"

def test_predict_missing_field():
    payload = valid_payload.copy()
    payload.pop("soil_moisture_0600")
    response = client.post("/irrigation/predict", json=payload)
    # FastAPI validation should return 422
    assert response.status_code == 422

def test_predict_invalid_type():
    payload = valid_payload.copy()
    payload["days_after_sowing"] = "invalid"
    response = client.post("/irrigation/predict", json=payload)
    assert response.status_code == 422
