from sqlalchemy import Column, Integer, String
from app.database import Base

class Roles(Base):
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)