from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.goal_register import GoalRegister

from app.schemas.registration import  GoalRegisterResponse

router = APIRouter(prefix="/goal", tags=["goals"])

@router.get("/", 
    summary="Цели регистрации",
    response_model=list[GoalRegisterResponse])
async def get_goals(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(GoalRegister))
        goals = result.scalars().all()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return goals