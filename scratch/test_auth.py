from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)
# Register a user
reg_resp = client.post('/auth/register', json={
    'full_name': 'Test User',
    'email': 'test@example.com',
    'password': 'secret123'
})
print('Register status:', reg_resp.status_code)
print('Register body:', reg_resp.json())
# Login with correct credentials
login_resp = client.post('/auth/login', json={
    'email': 'test@example.com',
    'password': 'secret123'
})
print('Login status:', login_resp.status_code)
print('Login body:', login_resp.json())
# Login with wrong password
bad_login = client.post('/auth/login', json={
    'email': 'test@example.com',
    'password': 'wrongpwd'
})
print('Bad login status:', bad_login.status_code)
print('Bad login body:', bad_login.json())
