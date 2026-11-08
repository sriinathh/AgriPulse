import requests, json
url = 'http://127.0.0.1:8001/sensor/readings'
payload = {
    "sensor_id": "SM004",
    "field_id": "F005",
    "timestamp": "2023-01-01T12:00:00Z",
    "measurement_type": "temperature",
    "value": 25.0,
    "unit": "C",
    "quality_status": "good"
}
resp = requests.post(url, json=payload)
print('Status:', resp.status_code)
print('Response:', resp.text)
