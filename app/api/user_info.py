from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import os
import shutil
from fastapi import UploadFile, File

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

    if not current_user.image_path:
        current_user.image_path = "https://runtastic.gottland.ru/static/avatars/profile_placeholder.png"
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

# @router.post("/logout",
#     summary="Выход пользователя с аккаунта",
#     description="Выйти с аккаунта")
# async def logout(
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db)
# ):

#     current_user.jwt_reload = None
#     await db.commit()
#     return {"message": "Выход выполнен"}

@router.post("/photo",
    summary="Загрузка фото профиля",
    description="Загружает фото пользователя. Форматы: jpg, jpeg, png. Максимум 5 МБ.")
async def upload_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in {"jpg", "jpeg", "png"}:
        raise HTTPException(status_code=400, detail="Формат не поддерживается. Используйте jpg, jpeg или png")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Файл слишком большой. Максимум 5 МБ")

    # Удаляем старое фото если есть
    if current_user.image_path:
        old_file = current_user.image_path.replace("https://runtastic.gottland.ru/static/avatars/", "")
        old_path = os.path.join("app/static/avatars", old_file)
        if os.path.exists(old_path):
            os.remove(old_path)

    filename = f"{current_user.user_id}.{ext}"
    file_path = os.path.join("app/static/avatars", filename)

    with open(file_path, "wb") as f:
        f.write(contents)

    # Обновляем путь в БД
    current_user.image_path = f"https://runtastic.gottland.ru/static/avatars/{filename}"
    await db.commit()

    return {"image_path": current_user.image_path}

@router.delete("/photo",
    summary="Удаление фото профиля")
async def delete_photo(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.image_path:
        raise HTTPException(status_code=404, detail="Фото не найдено")

    # Удаляем файл
    filename = current_user.image_path.replace("https://runtastic.gottland.ru/static/avatars/", "")
    file_path = os.path.join("app/static/avatars", filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    current_user.image_path = None
    await db.commit()

    return {"message": "Фото удалено"}