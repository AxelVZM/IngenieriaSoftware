from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
from datetime import date

class CycleCreate(BaseModel):
    name: str
    start_date: date
    end_date: date
    duration_months: int
    status: str = "open"

    @field_validator("duration_months")
    @classmethod
    def duration_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("La duración en meses debe ser mayor que 0")
        return v

    @model_validator(mode="after")
    def end_after_start(self):
        if self.end_date <= self.start_date:
            raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio")
        return self

class CycleUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_months: Optional[int] = None
    status: Optional[str] = None

    @field_validator("duration_months")
    @classmethod
    def duration_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("La duración en meses debe ser mayor que 0")
        return v

    @model_validator(mode="after")
    def end_after_start(self):
        # Solo valida si ambas fechas vienen en la actualización
        if self.start_date is not None and self.end_date is not None:
            if self.end_date <= self.start_date:
                raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio")
        return self
