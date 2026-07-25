from pydantic import BaseModel
from typing import Optional
from datetime import date

class CycleCreate(BaseModel):
    name: str
    start_date: date
    end_date: date
    duration_months: int
    status: str = "open"

class CycleUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_months: Optional[int] = None
    status: Optional[str] = None
