from sqlalchemy import Column, Integer, Float, Boolean, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class ActivityMetInfo(Base):
    __tablename__ = "activity_met_info"

    met_info_id = Column(Integer, primary_key=True, autoincrement=True)
    type_activ_id = Column(Integer, ForeignKey("activity_types.type_activ_id"), nullable=False, unique=True)
    base_met = Column(Float, nullable=False)
    uses_speed_zones = Column(Boolean, default=False, nullable=False)

    zones = relationship("ActivityMetZone", back_populates="met_info", cascade="all, delete-orphan")