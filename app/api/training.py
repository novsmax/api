from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.activity_types import ActivityType
from app.schemas.training import TypeAcrivity

router = APIRouter(prefix="/training", tags=["training"])

@router.get("/types_activity", 
    summary="Виды активности",
    response_model=list[TypeAcrivity])
async def get_goals(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(ActivityType))
        types_activity = result.scalars().all()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return types_activity