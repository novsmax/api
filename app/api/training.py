from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, date
import uuid

from app.models.user import User
from app.services.cassandra import cassandra_service
from app.services.training_postgres import training_service
from app.core.dependencies import get_current_user

from app.database import get_db
from app.models.activity_types import ActivityType
from app.schemas.training import (
    TypeAcrivity, 
    StartTrainingResponce, 
    StartTrainingRequest,  
    GetActiveTrainingResponse,
    SendGPSPointsRequest,
    SendGPSPointsResponce,
    SaveTrainigResponce,
    SaveTrainigRequest)

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

@router.delete("/{training_id}/delete",
    summary = "Удалить активную тренировку (для тестов, убрать потом)",
    description=""
)
async def delete_trainig(
    training_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
):
    active_training = cassandra_service.get_active_training(current_user.user_id)
    if not active_training:
        raise HTTPException(status_code=404, detail="Нет активной тренировки")

    try:
        cassandra_service.delete_training(
            user_id = current_user.user_id,
            active_training_id = training_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "Тренировка удалена"}

@router.post("/{training_id}/gps_points",
    summary = "Отправить блок gps точек",
    description="Принимает и записчывает точки из мобильноно приложения на сервер",
    response_model = SendGPSPointsResponce
)
async def send_gps_pints(
    training_id: uuid.UUID,
    request: SendGPSPointsRequest,
    current_user: User = Depends(get_current_user)
):
    active_training = cassandra_service.get_active_training(current_user.user_id)
    if not active_training or active_training.active_training_id != training_id:
        raise HTTPException(status_code=404, detail="Тренировка не найдена")

    batch_exists = cassandra_service.check_batch_exists(training_id, request.batch_id)
    if batch_exists:
        return SendGPSPointsResponce(saved = 0, message = "Блок был уже сохранен ранее")
    
    points_data = [ 
        {
            "recorded_at": point.recorded_at,
            "latitude": point.latitude,
            "longitude": point.longitude,
            "accuracy": point.accuracy,
            "altitude": point.altitude,
            "speed": point.speed
        }
        for point in request.points
    ]

    try: 
        cassandra_service.save_gps_points(
            active_training_id = training_id, 
            batch_id = request.batch_id, 
            points = points_data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return SendGPSPointsResponce(saved=len(request.points))

@router.post("/{training_id}/save_training",
    summary = "Завершить тренировку",
    description="Переносит все данные на сохранение в постгрес и удалет из касандры",
    response_model = SaveTrainigResponce
)
async def save_active_training(
    training_id: uuid.UUID,
    request: SaveTrainigRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    active_training = cassandra_service.get_active_training(current_user.user_id)
    if not active_training or active_training.active_training_id != training_id:
        raise HTTPException(status_code=404, detail="Тренировка не найдена")
    
    gps_points = cassandra_service.get_gps_points(training_id)
    
    try:
        await training_service.save_complete_training(
            db=db,
            training_id=training_id,
            user_id=current_user.user_id,
            type_activ_id=active_training.type_activ_id,
            date = active_training.date,
            time_start=active_training.time_start,
            time_end=request.time_end,
            kilocalories=request.total_kilocalories,
            gps_points=gps_points
        )
        
        cassandra_service.delete_gps_points(training_id)
        cassandra_service.delete_training(current_user.user_id, training_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return SaveTrainigResponce(training_id=training_id)

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