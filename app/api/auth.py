from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    NicknameCheckRequest, 
    NicknameCheckResponse, 
    UserCreate, 
    UserResponse, 
    UserLogin
)
from app.schemas.email_verification import (
    EmailVerificationRequest, 
    EmailVerificationCode, 
    EmailVerificationResponse,
    TokenResponse,
    RefreshTokenRequest
)
from app.services.auth import auth_service
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", 
    summary="Регистрация пользователя",
    description="После регистрации на email отправляется код подтверждения",
    response_model=dict)
async def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    try:
        user, code = await auth_service.register_user(db, user_data)
        
        return {
            "message": "Регистрация успешна. Проверьте email для получения кода подтверждения.",
            "email": user.email,
            "expires_in": settings.VERIFICATION_CODE_EXPIRE_MINUTES * 60,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify-email", 
    summary="Подтверждение кода после регистарции",
    description="При успешном подтверждении пользователь автоматически авторизуется и получает access и refresh токены",
    response_model=TokenResponse)
async def verify_email(
    request: EmailVerificationCode,
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await auth_service.verify_email(db, request.email, request.code)
        
        if not user:
            raise HTTPException(status_code=400, detail="Ошибка подтверждения")
        
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.user_id}
        )
        new_refresh_token  = create_refresh_token(
            data={"sub": user.email, "user_id": user.user_id}
        )
        
        user.jwt_reload = new_refresh_token 
        await db.commit()
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token 
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/resend-code", 
    summary="Повторная отправка кода подтверждения (регистарция)",
    description="Новый код будет доступен через 2 минуты после предыдущей отправки",
    response_model=EmailVerificationResponse)
async def resend_verification_code(
    request: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Повторная отправка кода подтверждения.
    Доступно через 2 минуты после предыдущей отправки.
    """
    try:
        code, expires_in = await auth_service.resend_verification_code(db, request.email)
        
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        
        return EmailVerificationResponse(
            message="Код подтверждения отправлен повторно",
            expires_at=expires_at,
            remaining_seconds=expires_in
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", 
    summary="Вход зарегестрированных пользователей",
    description="Вход в систему для уже подтвержденных пользователей",
    response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    
    if not user.is_active:
        raise HTTPException(
            status_code=401, 
            detail="Email не подтвержден. Проверьте почту для получения кода подтверждения."
        )
    
    if not verify_password(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.user_id}
    )
    new_refresh_token  = create_refresh_token(
        data={"sub": user.email, "user_id": user.user_id}
    )
    
    user.jwt_reload = new_refresh_token 
    await db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token 
    )

@router.post("/refresh", 
    summary="Обновление токенов",
    description="Обновление access token с помощью refresh token",
    response_model=TokenResponse)
async def refresh_tokens(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Обновление access token с помощью refresh token.
    """
    try:
        payload = jwt.decode(
            request.refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Неверный тип токена")
        
        email = payload.get("sub")
        user_id = payload.get("user_id")
        if not email or not user_id:
            raise HTTPException(status_code=401, detail="Неверный токен")
        
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user or user.jwt_reload != request.refresh_token:
            raise HTTPException(status_code=401, detail="Неверный refresh токен")
        
        new_access_token = create_access_token(
            data={"sub": user.email, "user_id": user.user_id}
        )
        new_refresh_token = create_refresh_token(
            data={"sub": user.email, "user_id": user.user_id}
        )
        
        user.jwt_reload = new_refresh_token
        await db.commit()
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token
        )
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Неверный токен")

@router.post("/check-nickname", 
    summary="Проверка доступности nickname",
    description="Проверка доступности nickname",
    response_model=NicknameCheckResponse)
async def check_nickname(
    request: NicknameCheckRequest,
    db: AsyncSession = Depends(get_db)
):
    is_available, message = await auth_service.check_nickname_unique(
        db, 
        request.nickname
    )
    
    return NicknameCheckResponse(
        nickname=request.nickname,
        is_available=is_available,
        message=message
    )

@router.post("/logout",
    summary="Выход пользователя с аккаунта",
    description="Выйти с аккаунта")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):

    current_user.jwt_reload = None
    await db.commit()
    return {"message": "Выход выполнен"}