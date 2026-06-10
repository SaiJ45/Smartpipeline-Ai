from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from api.auth import (
    create_access_token,
    get_password_hash,
    users,
    verify_password,
)


router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    password: str


@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users.get(form_data.username)
    if user is None or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user["username"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/register")
def register(request: RegisterRequest):
    if request.username in users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    users[request.username] = {
        "username": request.username,
        "hashed_password": get_password_hash(request.password),
    }

    return {
        "status": "success",
        "message": "User registered successfully",
    }
