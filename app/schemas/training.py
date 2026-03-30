from pydantic import BaseModel
from typing import List

class TypeAcrivity(BaseModel):
    type_activ_id: int
    name: str

    class Config:
        from_attributes = True