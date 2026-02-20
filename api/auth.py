"""Authentication: JWT tokens, password hashing, and FastAPI dependency."""

import time
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from storage.database import get_db, get_next_id

# --- Config ---
SECRET_KEY = "koinx-tax-auditor-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 86400  # 24 hours

# --- Password hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Bearer token scheme ---
bearer_scheme = HTTPBearer()


# --- Models ---
class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserOut(BaseModel):
    id: int
    email: str
    name: str


# --- Helpers ---
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int, email: str, name: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "name": name,
        "exp": time.time() + ACCESS_TOKEN_EXPIRE_SECONDS,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("exp", 0) < time.time():
            raise HTTPException(status_code=401, detail="Token expired")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# --- FastAPI dependency ---
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Extract and validate the current user from the JWT token."""
    payload = decode_token(credentials.credentials)
    return {
        "id": int(payload["sub"]),
        "email": payload["email"],
        "name": payload["name"],
    }


# --- Seed users helper ---
def seed_user(email: str, password: str, name: str):
    """Add a user to the database (for manual seeding)."""
    db = get_db()
    existing = db.users.find_one({"email": email})
    if existing:
        return
    user_id = get_next_id("users")
    db.users.insert_one({
        "id": user_id,
        "email": email,
        "password_hash": hash_password(password),
        "name": name,
        "created_at": time.time(),
    })
