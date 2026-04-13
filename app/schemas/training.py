from pydantic import BaseModel, Field
from typing import Optional, List
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

class GetActiveTrainingResponse(BaseModel):
    active_training_id: UUID
    type_activ_id: int
    date: str
    time_start: datetime
    training_time: int
    kilocalories: float

class GPSPoints(BaseModel):
    recorded_at: datetime
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    altitude: Optional[float] = None
    speed: Optional[float] = None
    calories: Optional[float] = None

class SendGPSPointsResponce(BaseModel):
    saved: int
    message: str = "Точки сохранены"

class SendGPSPointsRequest(BaseModel):
    batch_id: UUID
    points: List[GPSPoints] = Field(..., min_length=1, max_length=100)

class SaveTrainigResponce(BaseModel):
    training_id: UUID
    message: str = "Тренировка завершена"

class SaveTrainigRequest(BaseModel):
    time_end: datetime
    total_distance_meters: Optional[float] = None
    total_kilocalories: Optional[float] = None

class GetCompleteTrainingResponce(BaseModel):
    training_id: UUID
    type_activ_id: int
    date: str
    time_start: datetime
    time_end: Optional[datetime] = None
    kilocalories: Optional[float] = None
    gps_track: Optional[dict] = None

class MetZoneResponse(BaseModel):
    speed_min: Optional[float]
    speed_max: Optional[float]
    met_value: float

    class Config:
        from_attributes = True


class METActivityResponce(BaseModel):
    type_activ_id: int
    base_met: float
    uses_speed_zones: bool
    zones: list[MetZoneResponse] = []

    class Config:
        from_attributes = True