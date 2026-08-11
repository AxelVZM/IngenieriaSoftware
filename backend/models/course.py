from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date

class CourseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    base_price: float

    @field_validator("base_price")
    @classmethod
    def price_must_be_positive(cls, v):
        # El cero tampoco es un precio de venta válido: dejaba matricular un
        # curso gratuito por un simple error de tipeo.
        if v <= 0:
            raise ValueError("El precio base debe ser mayor que 0")
        return v

class CourseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: Optional[float] = None

    @field_validator("base_price")
    @classmethod
    def price_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("El precio base debe ser mayor que 0")
        return v

class CourseOfferingCreate(BaseModel):
    course_id: int
    cycle_id: int
    group_label: str
    teacher_id: Optional[int] = None
    price_override: Optional[float] = None
    capacity: Optional[int] = None

class CourseOfferingUpdate(BaseModel):
    group_label: Optional[str] = None
    teacher_id: Optional[int] = None
    price_override: Optional[float] = None
    capacity: Optional[int] = None

class ScheduleCreate(BaseModel):
    course_offering_id: int
    day_of_week: str
    start_time: str
    end_time: str
    classroom: Optional[str] = None

class ScheduleUpdate(BaseModel):
    day_of_week: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    classroom: Optional[str] = None
