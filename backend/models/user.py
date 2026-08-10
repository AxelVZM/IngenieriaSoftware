"""
Modelos Pydantic de usuario.

Estos modelos son la PRIMERA linea de validacion del backend: FastAPI rechaza
con 422 cualquier peticion que no cumpla, antes de llegar al controlador.
Con esto el sistema deja de depender del frontend para validar entradas.
"""

from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

DNI_PATTERN = re.compile(r"^\d{8}$")
ROLES_VALIDOS = {"admin", "teacher", "student"}


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    role: str

    @field_validator("username")
    @classmethod
    def limpiar_username(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El usuario no puede estar vacío")
        return v

    @field_validator("role")
    @classmethod
    def validar_role(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in ROLES_VALIDOS:
            raise ValueError(
                f"Rol inválido. Valores permitidos: {', '.join(sorted(ROLES_VALIDOS))}"
            )
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=72)
    related_id: Optional[int] = Field(default=None, ge=1)

    @field_validator("password")
    @classmethod
    def validar_password(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("La contraseña debe incluir al menos una letra y un número")
        return v


class UserLogin(BaseModel):
    """
    Credenciales de acceso.

    OJO: aqui NO se exige el formato de 8 digitos. El campo `dni` se usa
    tambien como `username` para las cuentas de admin y docente, que pueden
    tener un identificador distinto a un DNI. El formato estricto se valida
    solo en el registro de estudiantes (ver models/student.py).
    """

    dni: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1, max_length=72)

    @field_validator("dni")
    @classmethod
    def limpiar_dni(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El DNI o usuario es requerido")
        return v

    @field_validator("password")
    @classmethod
    def validar_password_no_vacio(cls, v: str) -> str:
        if not v:
            raise ValueError("La contraseña es requerida")
        return v


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    related_id: Optional[int] = None


class TokenResponse(BaseModel):
    token: str
    user: UserResponse