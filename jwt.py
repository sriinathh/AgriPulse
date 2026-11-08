"""Lightweight stub for jwt used in auth_service during tests.
Provides minimal encode/decode matching the interface used in the project.
"""
import json

class PyJWTError(Exception):
    pass

def encode(payload: dict, secret: str, algorithm: str) -> str:
    # Simple deterministic token – just dump payload as JSON
    return json.dumps(payload)

def decode(token: str, secret: str, algorithms: list):
    try:
        return json.loads(token)
    except Exception as exc:
        raise PyJWTError(str(exc))
