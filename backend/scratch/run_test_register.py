import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
payload = {"full_name": "Tmp User", "email": "tmpuser@example.com", "password": "TmpPass123"}
resp = client.post("/auth/register", json=payload)
print("Status:", resp.status_code)
print("Response JSON:", resp.json())
# If success, also try login
if resp.status_code == 200:
    login_resp = client.post("/auth/login", json={"email": payload["email"], "password": payload["password"]})
    print("Login status:", login_resp.status_code)
    print("Login JSON:", login_resp.json())
