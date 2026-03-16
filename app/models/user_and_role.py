from sqlalchemy import Column, Integer, ForeignKey
from app.database import Base

class UserAndRole(Base):
    __tablename__ = "user_and_role"

    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.role_id"), primary_key=True)