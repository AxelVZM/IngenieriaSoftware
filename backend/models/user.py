from pydantic import BaseModel
from typing import Optional
from datetime import date

class UserBase(BaseModel):
    username: str
    role: str

class UserCreate(UserBase):
    password: str
    related_id: Optional[int] = None

class UserLogin(BaseModel):
    dni: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    related_id: Optional[int] = None

class TokenResponse(BaseModel):
    token: str
    user: UserResponse
