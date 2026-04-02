from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class TypeAcrivity(BaseModel):
    type_activ_id: int
    name: str
    image_path: Optional[str] = None

    class Config:
        from_attributes = True

class StartTrainingResponce(BaseModel):
    active_training_id: UUID
    type_activ_id: int
    time_start: datetime
    message: str = "Тренировка начата"

class StartTrainingRequest(BaseModel):
    type_activ_id: int

class DeleteTrainingRequest(BaseModel):
    active_training_id: UUID

class GetActiveTrainingResponse(BaseModel):
    active_training_id: UUID
    type_activ_id: int
    date: str
    time_start: datetime
    training_time: int
    is_pause: bool
    kilocalories: float