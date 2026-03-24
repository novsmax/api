from sqlalchemy import Column, Integer, ForeignKey
from app.database import Base
from sqlalchemy.orm import relationship

class UserAndGoal(Base):
    __tablename__ = "user_and_goal"

    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    goal_id = Column(Integer, ForeignKey("goal_register.goal_id"), primary_key=True)

    user = relationship("User", back_populates="user_goals")