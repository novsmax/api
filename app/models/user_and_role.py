from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class UserAndRole(Base):
    __tablename__ = "user_and_role"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.role_id"), primary_key=True)

    user = relationship("User", back_populates="user_roles")