"""Authentication endpoints."""

from fastapi import APIRouter, HTTPException

from storage.database import get_db
from api.auth import LoginRequest, LoginResponse, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest):
    db = get_db()
    user = db.users.find_one({"email": body.email})

    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user["id"], user["email"], user["name"])

    return LoginResponse(
        access_token=token,
        user={"id": user["id"], "email": user["email"], "name": user["name"]},
    )
