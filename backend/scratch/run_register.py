import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
payload = {"full_name": "Tmp User", "email": "tmpuser@example.com", "password": "TmpPass123"}
response = client.post("/auth/register", json=payload)
print("Status:", response.status_code)
print("JSON:", response.json())
