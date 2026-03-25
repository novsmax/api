from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt, JWTError

from app.database import get_db
from app.models.user import User
from app.core.config import settings

bearer_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Неверный тип токена")
        
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Неверный токен")
            
    except JWTError:
        raise HTTPException(status_code=401, detail="Неверный или просроченный токен")
    
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Аккаунт не активен")
    
    return user