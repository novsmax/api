from sqlalchemy import Column, Integer, String
from app.database import Base

class Club(Base):
    __tablename__ = "clubs"

    club_id = Column(Integer, primary_key=True, autoincrement=True)
    club_name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    image_path = Column(String(500), nullable=True)