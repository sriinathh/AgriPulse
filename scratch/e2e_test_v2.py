import sys, os
from fastapi.testclient import TestClient

# Ensure backend is on PYTHONPATH
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_path not in sys.path:
    sys.path.append(backend_path)

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
print_resp('system/status', client.get('/system/status'))

# 2. Create farmer
farmer_payload = {"farmer_id": "F001", "name": "Test Farmer", "email": "test@example.com"}
print_resp('POST /farmers', client.post('/farmers', json=farmer_payload))

# 3. Create field linked to farmer
field_payload = {"farmer_id": "F001", "crop_type": "Corn", "name": "TestField"}
print_resp('POST /fields', client.post('/fields', json=field_payload))
field = client.post('/fields', json=field_payload).json()
field_id = field.get('field_id')

# 4. Create sensor linked to field
sensor_payload = {"field_id": field_id, "type": "soil_moisture", "model": "SM-1000"}
print_resp('POST /sensors', client.post('/sensors', json=sensor_payload))
sensor = client.post('/sensors', json=sensor_payload).json()
sensor_id = sensor.get('sensor_id')

# 5. Ingest reading
reading_payload = {"sensor_id": sensor_id, "timestamp": "2026-10-28T12:00:00Z", "value": 23.7}
print_resp('POST /sensor/readings', client.post('/sensor/readings', json=reading_payload))
reading = client.post('/sensor/readings', json=reading_payload).json()
reading_id = reading.get('id')

# 6. Retrieve reading
print_resp('GET /sensor/readings/{id}', client.get(f'/sensor/readings/{reading_id}'))

# 7. Prediction valid
pred_payload = {
    "field_id": field_id,
    "timestamp": "2026-10-28T12:05:00Z",
    "soil_moisture_0600": 24.5,
    "soil_moisture_change_24h": 0.3,
    "temperature_0600": 22.1,
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
print_resp('POST /irrigation/predict valid', client.post('/irrigation/predict', json=pred_payload))

# 8. Prediction invalid (missing required field)
invalid_payload = {"field_id": field_id, "timestamp": "2026-10-28T12:05:00Z"}
print_resp('POST /irrigation/predict invalid', client.post('/irrigation/predict', json=invalid_payload))
