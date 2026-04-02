from sqlalchemy import Column, Integer, Float, Date, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import uuid

class CompletedTraining(Base):
    __tablename__ = "completed_training"

    training_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    type_activ_id = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    time_start = Column(DateTime(timezone=True), nullable=False)
    time_end = Column(DateTime(timezone=True), nullable=True)
    data_training = Column(Text, nullable=True)
    kilocalories = Column(Float, nullable=True)