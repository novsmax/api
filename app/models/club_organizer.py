from sqlalchemy import Column, Integer, ForeignKey
from app.database import Base

class ClubOrganizer(Base):
    __tablename__ = "club_organizer"

    club_organizer_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.role_id"), nullable=False)
    club_id = Column(Integer, ForeignKey("clubs.club_id"), nullable=True)