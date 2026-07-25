from pydantic import BaseModel
from typing import Optional

class TeacherCreate(BaseModel):
    first_name: str
    last_name: str
    dni: str
    phone: str
    email: str
    specialization: Optional[str] = None

class TeacherUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dni: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    specialization: Optional[str] = None

class TeacherResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    dni: str
    phone: str
    email: str
    specialization: Optional[str] = None

class AttendanceCreate(BaseModel):
    schedule_id: int
    student_id: int
    status: str
    date: str
