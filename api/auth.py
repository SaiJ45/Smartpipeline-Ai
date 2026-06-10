from datetime import datetime, timedelta
import os

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.handlers.bcrypt import bcrypt

from config.settings import get_settings


SECRET_KEY = get_settings().JWT_SECRET
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

os.environ.setdefault("PASSLIB_BUILTIN_BCRYPT", "enabled")
bcrypt.set_backend("builtin")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=4)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def verify_password(plain, hashed) -> bool:
    return pwd_context.verify(plain, hashed)


def get_password_hash(password) -> str:
    return pwd_context.hash(password)


users = {
    "admin": {
        "username": "admin",
        "hashed_password": get_password_hash("admin123"),
    }
}


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    if username not in users:
        raise credentials_exception

    return username
