from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional

class EmailVerificationRequest(BaseModel):
    email: EmailStr

class EmailVerificationCode(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)

class EmailVerificationResponse(BaseModel):
    message: str
    expires_at: Optional[datetime]
    remaining_seconds: Optional[int]

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str