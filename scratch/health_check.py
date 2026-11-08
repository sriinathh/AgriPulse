from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)
resp = client.get('/health')
print('STATUS', resp.status_code)
print('BODY', resp.json())
