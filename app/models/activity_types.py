from sqlalchemy import Column, Integer, String
from app.database import Base

class ActivityType(Base):
    __tablename__ = "activity_types"

    type_activ_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    image_path = Column(String(255), nullable=True)