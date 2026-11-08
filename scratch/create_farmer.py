import json, requests
url = 'http://127.0.0.1:8000/farmers'
payload = {
    "name": "Test Farmer",
    "phone": "1234567890",
    "email": "test@example.com"
}
resp = requests.post(url, json=payload)
print('Status:', resp.status_code)
print('Body:', resp.text)
