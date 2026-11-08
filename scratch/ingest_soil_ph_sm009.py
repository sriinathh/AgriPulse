import requests, datetime
url = 'http://127.0.0.1:8001/sensor/readings'
payload = {
    "sensor_id": "SM009",
    "field_id": "test_field_verify_1",
    "timestamp": datetime.datetime.utcnow().isoformat(),
    "measurement_type": "soil_ph",
    "value": 6.5,
    "unit": "pH",
    "quality_status": "good",
    "is_simulated": True,
}
resp = requests.post(url, json=payload)
print('Status:', resp.status_code)
print('Response:', resp.text)
