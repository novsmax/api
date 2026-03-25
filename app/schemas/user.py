from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import date, datetime
from typing import List, Optional

class UserBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    birth_date: date
    gender: str = Field(..., pattern="^(male|female)$")
    email: EmailStr
    nickname: str = Field(..., min_length=3, max_length=100)
    goal_ids: List[int] = Field(..., min_length=1, description="Список ID целей регистрации")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    confirm_password: str
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v: str, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Пароли не совпадают')
        return v
    

class UserResponse(UserBase):
    user_id: int
    is_active: bool = False
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class NicknameCheckRequest(BaseModel):
    nickname: str = Field(..., min_length=3, max_length=100)

class NicknameCheckResponse(BaseModel):
    nickname: str
    is_available: bool
    message: str

class GetUserInfo(BaseModel):
    first_name: str
    last_name: Optional[str]
    middle_name: Optional[str]
    birth_date: date
    weight: Optional[float]
    height: Optional[float]
    gender: str = Field(..., pattern="^(male|female)$")
    nickname: str

    class Config:
        from_attributes = True

class EditUserInfoRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    birth_date: Optional[date] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    gender: Optional[str] = Field(default=None, pattern="^(male|female)$")
    nickname: Optional[str] = None