import requests, json, sys
url = 'http://127.0.0.1:8001/sensor/readings?measurement_type=soil_ph&limit=100'
resp = requests.get(url)
print('Status', resp.status_code)
print('Body', resp.text[:500])
