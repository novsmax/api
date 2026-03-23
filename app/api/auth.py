from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
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
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirm
)
from app.services.auth import auth_service
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, verify_password

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=dict)
async def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Регистрация нового пользователя.
    После регистрации на email отправляется код подтверждения.
    """
    try:
        user, code = await auth_service.register_user(db, user_data)
        
        return {
            "message": "Регистрация успешна. Проверьте email для получения кода подтверждения.",
            "email": user.email,
            "expires_in": settings.VERIFICATION_CODE_EXPIRE_MINUTES * 60,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify-email", response_model=TokenResponse)
async def verify_email(
    request: EmailVerificationCode,
    db: AsyncSession = Depends(get_db)
):
    """
    Подтверждение email с помощью кода из письма.

    При успешном подтверждении пользователь автоматически авторизуется
    и получает access и refresh токены.
    """
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

@router.post("/resend-code", response_model=EmailVerificationResponse)
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
        
        expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        return EmailVerificationResponse(
            message="Код подтверждения отправлен повторно",
            expires_at=expires_at,
            remaining_seconds=expires_in
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Вход в систему для уже подтвержденных пользователей.
    """
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

@router.post("/refresh", response_model=TokenResponse)
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

@router.post("/check-nickname", response_model=NicknameCheckResponse)
async def check_nickname(
    request: NicknameCheckRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Проверка доступности nickname.
    """
    is_available, message = await auth_service.check_nickname_unique(
        db, 
        request.nickname
    )
    
    return NicknameCheckResponse(
        nickname=request.nickname,
        is_available=is_available,
        message=message
    )

@router.post("/password-reset/request")
async def request_password_reset(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Запрос сброса пароля
    """

    await auth_service.request_password_reset(db, request.email)
    
    return {"message": "Если email существует и подтверждён — код отправлен"}

@router.post("/password-reset/confirm", response_model=TokenResponse)
async def confirm_password_reset(
    request: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """
    Подтверждение сброса пароля
    """
    try:
        user = await auth_service.confirm_password_reset(
            db, 
            request.email, 
            request.code, 
            request.password
        )

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