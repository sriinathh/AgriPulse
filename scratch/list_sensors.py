import requests, json
url = 'http://127.0.0.1:8001/sensors'
resp = requests.get(url)
print('Status:', resp.status_code)
print('Body:', resp.text)
