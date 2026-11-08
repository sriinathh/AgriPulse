"""Authentication utilities.

Provides password hashing (using argon2-cffi) and JWT token creation / verification.

passlib+bcrypt is avoided because passlib 1.7.4 is incompatible with bcrypt ≥ 4.x
(missing ``bcrypt.__about__`` attribute). argon2-cffi is a modern, self-contained
alternative that ships its own bindings and needs no external bcrypt binary.
"""

from datetime import datetime, timedelta
from typing import Optional

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

from app.config import get_settings

# Argon2id hasher – OWASP-recommended defaults
_ph = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash a plain password with Argon2id."""
    return _ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its Argon2id hash.
    Returns False if the hash format is unknown or verification fails.
    """
    try:
        return _ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError, Exception):
        return False


def create_access_token(user_id: int) -> str:
    """Create a JWT token for a given user ID.

    The token contains the user ID and expiration time.
    """
    settings = get_settings()
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expiration_minutes)
    to_encode = {"sub": str(user_id), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[int]:
    """Decode JWT and return user ID if valid, otherwise ``None``."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    except jwt.PyJWTError:
        return None


def get_current_user(authorization: Optional[str] = None) -> int:
    """Dependency placeholder. Actual dependency is implemented in routers."""
    from fastapi import Header, HTTPException, status
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header")
    token = authorization.split(" ")[1]
    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    return user_id
