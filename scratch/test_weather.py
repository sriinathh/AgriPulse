import sys, os
sys.path.append(r"C:\\Users\\Arpitha Medharametla\\Documents\\smart-irrigation\\backend")
from app.main import app
from fastapi.testclient import TestClient
client = TestClient(app)
resp = client.get('/weather/geocode?q=Nizamabad')
print('GEOCODE status', resp.status_code)
print('GEOCODE json', resp.json())
resp2 = client.get('/weather/live-by-coords?latitude=18.6725&longitude=78.1044')
print('LIVE status', resp2.status_code)
print('LIVE json', resp2.json())
