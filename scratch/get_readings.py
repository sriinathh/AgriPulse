import requests, json, sys
url = 'http://127.0.0.1:8001/sensor/readings?limit=10'
try:
    r = requests.get(url)
    print('Status:', r.status_code)
    print('Body:', r.text)
except Exception as e:
    print('Error:', e)
    sys.exit(1)
