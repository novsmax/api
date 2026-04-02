from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt
from typing import Optional
import random
import string

from app.core.config import settings

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if "user_id" in to_encode and not isinstance(to_encode["user_id"], str):
        to_encode["user_id"] = str(to_encode["user_id"])
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    if "user_id" in to_encode and not isinstance(to_encode["user_id"], str):
        to_encode["user_id"] = str(to_encode["user_id"])
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def generate_verification_code(length: int = 6) -> str:
    """Генерирует числовой код верификации"""
    return ''.join(random.choices(string.digits, k=length))