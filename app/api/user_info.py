from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database import get_db
from app.models.user import User
from app.schemas.user import GetUserInfo, EditUserInfoRequest

from app.services.auth import auth_service

router = APIRouter(prefix="/user", tags=["user_info"])

@router.get("/", 
    summary="Инофрмация о пользователе",
    description="Получить информацию о пользователе по его email",
    response_model=GetUserInfo)
async def user_info(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    user = await db.execute(
        select(User).where(User.email == email)
    )
    user = user.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return user

@router.patch("/edit", 
    summary="Редактирование информации о пользователе",
    description="Редактировать информацию о пользователе по его email",
    response_model=GetUserInfo)
async def user_info(
    email: str,
    request: EditUserInfoRequest,
    db: AsyncSession = Depends(get_db)
):
    user = await db.execute(
        select(User).where(User.email == email)
    )
    user = user.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if request.nickname and request.nickname != user.nickname:
        flag, message = await auth_service.check_nickname_unique(db, request.nickname)
        if not flag:
            raise HTTPException(status_code=400, detail=message)

    update_info = request.model_dump(exclude_unset=True)
    for field, value in update_info.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return user

@router.delete("/delete",
    summary="Удаление пользователя по его email",
    description="Удалить пользователя по его email",)
async def delete_user(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    user = await db.execute(
        select(User).where(User.email == email)
    )
    user = user.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    await db.delete(user)
    await db.commit()

    return {"message": "Пользователь удалён"}