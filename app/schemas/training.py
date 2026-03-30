from pydantic import BaseModel
from typing import Optional

class TypeAcrivity(BaseModel):
    type_activ_id: int
    name: str
    image_path: Optional[str] = None

    class Config:
        from_attributes = True