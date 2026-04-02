from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class TrainingGPSPoints(Base):
    __tablename__ = "training_gps_points"

    gps_id = Column(Integer, primary_key=True, autoincrement=True)
    training_id = Column(
        UUID(as_uuid=True),
        ForeignKey("completed_training.training_id"),
        nullable=False,
        index=True
    )
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, nullable=True)
    speed = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)