from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.roles import Roles
from app.models.user import User
from app.models.user_and_role import UserAndRole

from app.schemas.registration import RoleResponse
from app.core.dependencies import get_current_user

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
    summary="Поулчение роли пользователя",
    response_model=list[RoleResponse])
async def user_roles(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ):

    try:
        result = await db.execute(
            select(Roles)
            .join(UserAndRole, Roles.role_id == UserAndRole.role_id)
            .where(UserAndRole.user_id == current_user.user_id)
        )
        roles = result.scalars().all()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return roles