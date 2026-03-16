from pydantic import BaseModel
from typing import List

class GoalRegisterResponse(BaseModel):
    goal_id: int
    description: str
    id_role: int

    class Config:
        from_attributes = True

class RoleResponse(BaseModel):
    role_id: int
    name: str

    class Config:
        from_attributes = True