from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database import get_db
from app.models.user import User
from app.schemas.user import GetUserInfo, EditUserInfoRequest

from app.services.auth import auth_service

from app.core.dependencies import get_current_user

router = APIRouter(prefix="/user", tags=["user_info"])

@router.get("/", 
    summary="Инофрмация о пользователе",
    description="Получить информацию о пользователе по access токену",
    response_model=GetUserInfo)
async def user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):

    return current_user

@router.patch("/edit", 
    summary="Редактирование информации о пользователе",
    description="Редактировать информацию о пользователе по его access токену",
    response_model=GetUserInfo)
async def user_info(
    request: EditUserInfoRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if request.nickname and request.nickname != current_user.nickname:
        flag, message = await auth_service.check_nickname_unique(db, request.nickname)
        if not flag:
            raise HTTPException(status_code=400, detail=message)

    update_info = request.model_dump(exclude_unset=True)
    for field, value in update_info.items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)

    return current_user

@router.delete("/delete",
    summary="Удаление пользователя",
    description="Удалить пользователя по access токену (удалить свой профиль)")
async def delete_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):

    await db.delete(current_user)
    await db.commit()

    return {"message": "Пользователь удалён"}

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