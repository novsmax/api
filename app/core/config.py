from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str
    
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    POSTGRES_PORT: Optional[str] = "5432"
    
    SERVER_HOST: Optional[str] = None
    SERVER_PORT: Optional[int] = None
    SERVER_USER: Optional[str] = None
    SERVER_PASSWORD: Optional[str] = None
    
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    EMAIL_FROM: str
    
    VERIFICATION_CODE_LENGTH: int = 6
    VERIFICATION_CODE_EXPIRE_MINUTES: int = 10
    VERIFICATION_CODE_EXPIRE_MINUTES_PASSWORD_RESET: int = 10
    MAX_VERIFICATION_ATTEMPTS: int = 5
    RESEND_COOLDOWN_SECONDS: int = 120
    
    class Config:
        env_file = ".env"
        extra = "ignore" 

settings = Settings()