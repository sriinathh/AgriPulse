import json, sys
import requests
from pathlib import Path

def main():
    url = 'http://127.0.0.1:8001/sensor/readings'
    payload = {
        "sensor_id": "SM004",
        "field_id": "F005",
        "timestamp": "2026-10-30T10:00:00Z",
        "measurement_type": "temperature",
        "value": 25.3,
        "unit": "C"
    }
    try:
        resp = requests.post(url, json=payload)
        print('POST status', resp.status_code)
        print(resp.text)
    except Exception as e:
        print('Error', e)
        sys.exit(1)

if __name__ == '__main__':
    main()
