from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from typing import Literal, Optional

from app.database.session import get_db
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.auth_service import hash_password, verify_password, create_access_token, decode_access_token

import logging

router = APIRouter(prefix="/auth", tags=["auth"])
log = logging.getLogger("auth")

# ----- Data models -----
class RegisterRequest(BaseModel):
    full_name: str
    email: str  # using plain string to avoid email-validator dependency
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"

# ----- Helper -----
def get_current_user(authorization: str = Header(None, convert_underscores=False)) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header")
    token = authorization.split(" ")[1]
    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    return user_id

# ----- Endpoints -----
# ----- Endpoints -----
@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    # Validate email not already taken
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    # Hash password securely (bcrypt via passlib)
    hashed = hash_password(req.password)

    # Create User record
    user = User(full_name=req.full_name, email=req.email, hashed_password=hashed)
    db.add(user)

    # Also create a Farmer record linked by email (if not already present)
    from app.models.farmer import Farmer
    from uuid import uuid4
    farmer_exists = db.query(Farmer).filter(Farmer.email == req.email).first()
    if not farmer_exists:
        farmer = Farmer(
            farmer_id=uuid4().hex[:32],
            name=req.full_name,
            email=req.email,
            is_demo=False,
        )
        db.add(farmer)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        log.exception("Registration failed during commit")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Registration failed")
    db.refresh(user)
    token = create_access_token(user.id)
    return {"access_token": token}



@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    token = create_access_token(user.id)
    return {"access_token": token}

@router.get("/me")
def me(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Also look for associated Farmer phone or details
    from app.models.farmer import Farmer
    farmer = db.query(Farmer).filter(Farmer.email == user.email).first()
    phone = farmer.phone if farmer else None

    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "phone": phone,
    }


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


@router.put("/me")
def update_me(req: UpdateProfileRequest, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    from app.models.farmer import Farmer
    old_email = user.email

    if req.email and req.email.strip().lower() != user.email.lower():
        new_email = req.email.strip().lower()
        conflict = db.query(User).filter(User.email == new_email).first()
        if conflict:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")
        user.email = new_email

    if req.full_name and req.full_name.strip():
        user.full_name = req.full_name.strip()

    # Update or create linked Farmer profile
    farmer = db.query(Farmer).filter(Farmer.email == old_email).first()
    if not farmer and old_email != user.email:
        farmer = db.query(Farmer).filter(Farmer.email == user.email).first()
    
    if farmer:
        farmer.name = user.full_name
        farmer.email = user.email
        if req.phone is not None:
            farmer.phone = req.phone.strip()
    else:
        from uuid import uuid4
        farmer = Farmer(
            farmer_id=uuid4().hex[:32],
            name=user.full_name,
            email=user.email,
            phone=req.phone.strip() if req.phone else None,
            is_demo=False,
        )
        db.add(farmer)

    db.commit()
    db.refresh(user)
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "phone": farmer.phone if farmer else req.phone,
    }

# ----- Password reset endpoint -----
from pydantic import BaseModel

class ResetPasswordRequest(BaseModel):
    email: str
    new_password: str

@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset a user's password.
    This endpoint is intended for accounts whose stored password hash is malformed
    or uses an unsupported algorithm. It re‑hashes the new password with bcrypt
    and updates the database.
    """
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.hashed_password = hash_password(req.new_password)
    db.add(user)
    db.commit()
    return {"detail": "Password updated successfully"}
