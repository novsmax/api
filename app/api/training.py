from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, date
import uuid

from app.models.user import User
from app.services.cassandra import cassandra_service
from app.core.dependencies import get_current_user

from app.database import get_db
from app.models.activity_types import ActivityType
from app.schemas.training import (
    TypeAcrivity, 
    StartTrainingResponce, 
    StartTrainingRequest, 
    DeleteTrainingRequest, 
    GetActiveTrainingResponse)

router = APIRouter(prefix="/training", tags=["training"])

@router.post("/start",
    summary = "Начать тренировку",
    description="Создаёт активную тренировку в Cassandra. UUID генерируется клиентом",
    response_model=StartTrainingResponce
)
async def start_trainig(
    request: StartTrainingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    activity = await db.execute(
        select(ActivityType).where(ActivityType.type_activ_id == request.type_activ_id)
    )
    if not activity.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Нет такого вида активности")

    active_training_id_server = uuid.uuid4()    

    active_training = cassandra_service.get_active_training(current_user.user_id)
    if active_training:
        raise HTTPException(status_code=400, detail="У вас есть активная тренировка")

    try:
        cassandra_service.start_training(
            user_id = current_user.user_id,
            active_training_id = active_training_id_server,
            type_activ_id = request.type_activ_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return StartTrainingResponce(
        active_training_id=active_training_id_server,
        type_activ_id = request.type_activ_id,
        time_start = datetime.now(timezone.utc)
        )

@router.get("/active",
    summary = "Аткивная тренировка",
    description="Получить активную тренировку пользователя",
    response_model=GetActiveTrainingResponse
)
async def get_active_training(
    current_user: User = Depends(get_current_user)
):
    active_training = cassandra_service.get_active_training(current_user.user_id)
    if not active_training:
        raise HTTPException(status_code=404, detail="Нет активной тренировки")
    
    return GetActiveTrainingResponse(
        active_training_id=active_training.active_training_id,
        type_activ_id=active_training.type_activ_id,
        date=str(active_training.date),
        time_start=active_training.time_start,
        training_time=active_training.training_time,
        is_pause=active_training.is_pause,
        kilocalories=active_training.kilocalories
    )

@router.delete("/delete",
    summary = "Удалить активную тренировку (для тестов, убрать потом)",
    description="",
)
async def delete_trainig(
    request: DeleteTrainingRequest,
    current_user: User = Depends(get_current_user),
):
    active_training = cassandra_service.get_active_training(current_user.user_id)
    if not active_training:
        raise HTTPException(status_code=404, detail="Нет активной тренировки")

    cassandra_service.delete_training(
        user_id = current_user.user_id,
        active_training_id = request.active_training_id
    )

    return {"message": "Тренировка удалена"}


@router.get("/types_activity", 
    summary="Виды активности",
    response_model=list[TypeAcrivity])
async def get_goals(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(ActivityType))
        types_activity = result.scalars().all()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    for item in types_activity:
        if item.image_path:
            item.image_path = f"https://runtastic.gottland.ru/static/icons/{item.image_path}"
        else:
            item.image_path = f"https://runtastic.gottland.ru/static/icons/placeholder.png"
    return types_activity