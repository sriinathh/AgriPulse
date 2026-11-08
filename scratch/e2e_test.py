import json
import sys
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def print_resp(name, resp):
    print(f'=== {name} ===')
    print('Status:', resp.status_code)
    try:
        print('JSON:', resp.json())
    except Exception:
        print('Text:', resp.text)
    print()

# 1. System status
resp = client.get('/system/status')
print_resp('system/status', resp)

# 2. Create field
field_payload = {
    "farmer_id": "F001",
    "crop_type": "Corn",
    "name": "TestField"
}
resp = client.post('/fields', json=field_payload)
print_resp('POST /fields', resp)
field = resp.json()
field_id = field.get('field_id')

# 3. Create sensor linked to field
sensor_payload = {
    "field_id": field_id,
    "type": "soil_moisture",
    "model": "SM-1000"
}
resp = client.post('/sensors', json=sensor_payload)
print_resp('POST /sensors', resp)
sensor = resp.json()
sensor_id = sensor.get('sensor_id')

# 4. Ingest reading
reading_payload = {
    "sensor_id": sensor_id,
    "timestamp": "2026-10-28T12:00:00Z",
    "value": 23.7
}
resp = client.post('/sensor/readings', json=reading_payload)
print_resp('POST /sensor/readings', resp)
reading = resp.json()
reading_id = reading.get('id')

# 5. Retrieve reading
resp = client.get(f'/sensor/readings/{reading_id}')
print_resp('GET /sensor/readings/{id}', resp)

# 6. Prediction valid
pred_payload = {
    "field_id": field_id,
    "timestamp": "2026-10-28T12:05:00Z",
    "soil_moisture": 24.5,
    "temperature": 22.1,
    "humidity": 55.0,
    "rain_forecast_mm": 0.0
}
resp = client.post('/prediction', json=pred_payload)
print_resp('POST /prediction valid', resp)

# 7. Prediction invalid (missing soil_moisture)
invalid_payload = {"field_id": field_id, "timestamp": "2026-10-28T12:05:00Z"}
resp = client.post('/prediction', json=invalid_payload)
print_resp('POST /prediction invalid', resp)
