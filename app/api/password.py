from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.email_verification import (
    TokenResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordResetVerifyCode,
    PasswordResetResendCode
)
from app.services.auth import auth_service
from app.core.security import create_access_token, create_refresh_token

router = APIRouter(prefix="/password-reset", tags=["password"])

@router.post("/request",
    summary="Запрос кода для сброса пароля",
    description="Отправляется код для сброса на указанную почту")
async def request_password_reset(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        await auth_service.request_password_reset(db, request.email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {"message": "Если email существует и подтверждён — код отправлен"}

@router.post("/verify-code",
    summary="Подтверждение кода после сброса пароля",
    description="Новый код будет доступен через 2 минуты после предыдущей отправки")
async def verify_code_password_reset(
    request: PasswordResetVerifyCode,
    db: AsyncSession = Depends(get_db)
):
    try:
        await auth_service.verify_code_password(db, request.email, request.code)
        return {"message": "Код подтверждён"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/resend-verify-code",
    summary="Повторная отправка кода подтверждения (сброс пароля)",
    description="Новый код будет доступен через 2 минуты после предыдущей отправки")
async def resend_code_password_reset(
    request: PasswordResetResendCode,
    db: AsyncSession = Depends(get_db)
):
    try:
        await auth_service.resend_password_code(db, request.email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "Если email существует и подтверждён — код отправлен"}

@router.post("/confirm", 
    summary="Подтверждение нового пароля",
    description="При успешном подтверждении обновляется пароль пользователя",
    response_model=TokenResponse)
async def confirm_password_reset(
    request: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
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