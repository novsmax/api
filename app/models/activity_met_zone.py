from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class ActivityMetZone(Base):
    __tablename__ = "activity_met_zones"

    met_zone_id = Column(Integer, primary_key=True, autoincrement=True)
    activity_met_id = Column(Integer, ForeignKey("activity_met_info.met_info_id"), nullable=False)
    speed_min = Column(Float, nullable=True)
    speed_max = Column(Float, nullable=True)
    met_value = Column(Float, nullable=False)

    met_info = relationship("ActivityMetInfo", back_populates="zones")