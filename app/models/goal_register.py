from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base

class GoalRegister(Base):
    __tablename__ = "goal_register"

    goal_id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String(255), nullable=False)
    id_role = Column(Integer, ForeignKey("roles.role_id"), nullable=False)