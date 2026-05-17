from sqlalchemy import Column, String, Float, Date, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid

class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=True)    
    middle_name = Column(String(100), nullable=True)  
    birth_date = Column(Date, nullable=False)
    weight = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    gender = Column(String(10), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    nickname = Column(String(100), nullable=False, unique=True)
    image_path = Column(String(500), nullable=True)
    jwt_session = Column(String(500), nullable=True)
    jwt_reload = Column(String(500), nullable=True)
    password_reset_token_hash = Column(String(255), nullable=True)
    password_reset_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    email_verifications = relationship("EmailVerification", cascade="all, delete-orphan", back_populates="user")
    user_goals = relationship("UserAndGoal", cascade="all, delete-orphan", back_populates="user")
    user_roles = relationship("UserAndRole", cascade="all, delete-orphan", back_populates="user")
    trainer_profile = relationship("Trainer", cascade="all, delete-orphan", back_populates="user")
    club_organizer_profile = relationship("ClubOrganizer", cascade="all, delete-orphan", back_populates="user")
    completed_trainig_profile = relationship("CompletedTraining", cascade="all, delete-orphan", back_populates="user")