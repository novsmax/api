from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Optional
from datetime import date as date_type, datetime

from app.models.completed_training import CompletedTraining
from app.models.training_gps_points import TrainingGPSPoints

class TrainingService:

    async def save_complete_training(
        self,
        db: AsyncSession,
        training_id: UUID,
        user_id: int,
        type_activ_id: int,
        date,
        time_start,
        time_end,
        kilocalories: Optional[float],
        gps_points: list
    ):

        if not isinstance(date, date_type):
            date = date_type.fromisoformat(str(date))

        complete = CompletedTraining(
            training_id = training_id,
            user_id = user_id,
            type_activ_id = type_activ_id,
            date = date,
            time_start = time_start,
            time_end = time_end,
            kilocalories = kilocalories,
            data_training = None
        )

        db.add(complete)
        
        for point in gps_points:
            gps_record = TrainingGPSPoints(
                    training_id=training_id,
                    recorded_at=point.recorded_at,
                    latitude=point.latitude,
                    longitude=point.longitude,
                    altitude=point.altitude,
                    speed=point.speed,
                    accuracy=point.accuracy
                )
            db.add(gps_record)
        
        await db.commit()

training_service = TrainingService()