from pydantic import BaseModel
from typing import Optional

class StudentCreate(BaseModel):
    dni: str
    first_name: str
    last_name: str
    phone: str
    parent_name: str
    parent_phone: str
    password: str

class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None

class StudentResponse(BaseModel):
    id: int
    dni: str
    first_name: str
    last_name: str
    phone: str
    parent_name: str
    parent_phone: str
