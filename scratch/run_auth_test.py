import sys
sys.path.append(r"C:/Users/Arpitha Medharametla/Downloads/smart-irrigation")
from fastapi.testclient import TestClient
from backend.app.main import app
client = TestClient(app)
# Register
reg = client.post('/auth/register', json={'full_name':'Test User','email':'test@example.com','password':'secret123'})
print('Register', reg.status_code, reg.json())
# Login correct
login = client.post('/auth/login', json={'email':'test@example.com','password':'secret123'})
print('Login', login.status_code, login.json())
# Login wrong
bad = client.post('/auth/login', json={'email':'test@example.com','password':'wrong'})
print('Bad login', bad.status_code, bad.json())
