from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.roles import Roles
from app.models.user import User
from app.models.user_and_role import UserAndRole

from app.schemas.registration import RoleResponse

router = APIRouter(prefix="/role", tags=["roles"])

@router.get("/", 
    summary="Роли пользователей",
    response_model=list[RoleResponse])
async def roles(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Roles))
        roles = result.scalars().all()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return roles

@router.get("/user_roles", 
    summary="Поулчение роли пользователя по его email",
    response_model=list[RoleResponse])
async def user_roles(
        email: str,
        db: AsyncSession = Depends(get_db)
    ):

    try:
        user_result = await db.execute(
            select(User).where(User.email == email)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        result = await db.execute(
            select(Roles)
            .join(UserAndRole, Roles.role_id == UserAndRole.role_id)
            .where(UserAndRole.user_id == user.user_id)
        )
        roles = result.scalars().all()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return roles