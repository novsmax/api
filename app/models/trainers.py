from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Trainer(Base):
    __tablename__ = "trainers"

    trainer_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.role_id"), nullable=False)

    user = relationship("User", back_populates="trainer_profile")