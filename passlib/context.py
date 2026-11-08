'''Stub for passlib.context.CryptContext used in auth_service during tests.'''

class CryptContext:
    def __init__(self, schemes=None, deprecated=None):
        pass
    def hash(self, password: str) -> str:
        # Simple reversible hash for testing – prefix with 'hashed:'
        return f"hashed:{password}"
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return hashed_password == f"hashed:{plain_password}"
