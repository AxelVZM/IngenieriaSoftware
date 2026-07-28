"""
Modelos Pydantic de estudiante.

Los validadores de este archivo son la primera linea de validacion del
backend: FastAPI rechaza con 422 cualquier peticion que no cumpla, antes de
que el controlador toque la base de datos. Con esto el sistema deja de
depender del frontend para validar entradas.

Las mismas reglas se aplican en el registro (StudentCreate) y en la
actualizacion (StudentUpdate), con la diferencia de que en la actualizacion
todos los campos son opcionales: si llegan como None simplemente no se
validan porque no se van a modificar.
"""

from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Patrones y validadores compartidos
# ---------------------------------------------------------------------------

DNI_PATTERN = re.compile(r"^\d{8}$")
PHONE_PATTERN = re.compile(r"^9\d{8}$")  # celular peruano: 9 digitos, inicia en 9
NAME_PATTERN = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' .-]+$")


def _validar_dni(v: str) -> str:
    """Exige exactamente 8 digitos numericos."""
    v = v.strip()
    if not DNI_PATTERN.match(v):
        raise ValueError("El DNI debe tener exactamente 8 digitos numericos")
    return v


def _validar_telefono(v: str) -> str:
    """Limpia separadores y exige un celular peruano de 9 digitos."""
    v = re.sub(r"[\s()+-]", "", v.strip())
    if v.startswith("51") and len(v) == 11:  # tolera el prefijo de pais
        v = v[2:]
    if not PHONE_PATTERN.match(v):
        raise ValueError(
            "El telefono debe tener 9 digitos y comenzar con 9 (celular peruano)"
        )
    return v


def _validar_nombre(v: str) -> str:
    """Normaliza espacios, prohibe digitos y simbolos, y capitaliza."""
    v = re.sub(r"\s+", " ", v.strip())
    if len(v) < 2:
        raise ValueError("Debe tener al menos 2 caracteres")
    if not NAME_PATTERN.match(v):
        raise ValueError(
            "Solo puede contener letras, espacios, apostrofes y guiones"
        )
    return v.title()


def _validar_password(v: str) -> str:
    """Exige minimo 8 caracteres con al menos una letra y un numero."""
    if len(v.encode("utf-8")) > 72:
        # bcrypt ignora todo lo que pase de 72 bytes: se rechaza para que el
        # usuario no crea que su contrasena es mas larga de lo que realmente es.
        raise ValueError("La contrasena no puede superar los 72 bytes")
    if v.strip() != v:
        raise ValueError("La contrasena no puede empezar ni terminar con espacios")
    if not re.search(r"[A-Za-z]", v):
        raise ValueError("La contrasena debe incluir al menos una letra")
    if not re.search(r"\d", v):
        raise ValueError("La contrasena debe incluir al menos un numero")
    return v


# ---------------------------------------------------------------------------
# Modelos
# ---------------------------------------------------------------------------


class StudentCreate(BaseModel):
    """Datos de registro de un estudiante nuevo (RF01)."""

    # Los limites de Field son una barrera contra payloads absurdos; la regla
    # real (formato exacto) la aplican los validadores de abajo, que primero
    # limpian espacios y separadores.
    dni: str = Field(..., min_length=8, max_length=12)
    first_name: str = Field(..., min_length=2, max_length=60)
    last_name: str = Field(..., min_length=2, max_length=60)
    phone: str = Field(..., min_length=9, max_length=20)
    parent_name: str = Field(..., min_length=2, max_length=80)
    parent_phone: str = Field(..., min_length=9, max_length=20)
    password: str = Field(..., min_length=8, max_length=72)

    @field_validator("dni")
    @classmethod
    def validar_dni(cls, v: str) -> str:
        return _validar_dni(v)

    @field_validator("phone", "parent_phone")
    @classmethod
    def validar_telefono(cls, v: str) -> str:
        return _validar_telefono(v)

    @field_validator("first_name", "last_name", "parent_name")
    @classmethod
    def validar_nombre(cls, v: str) -> str:
        return _validar_nombre(v)

    @field_validator("password")
    @classmethod
    def validar_password(cls, v: str) -> str:
        return _validar_password(v)


class StudentUpdate(BaseModel):
    """
    Actualizacion parcial de un estudiante (RF03).

    El DNI no es actualizable a proposito: es el identificador de login y
    cambiarlo dejaria al estudiante sin acceso a su cuenta.
    """

    first_name: Optional[str] = Field(default=None, min_length=2, max_length=60)
    last_name: Optional[str] = Field(default=None, min_length=2, max_length=60)
    phone: Optional[str] = Field(default=None, min_length=9, max_length=20)
    parent_name: Optional[str] = Field(default=None, min_length=2, max_length=80)
    parent_phone: Optional[str] = Field(default=None, min_length=9, max_length=20)

    @field_validator("phone", "parent_phone")
    @classmethod
    def validar_telefono(cls, v: Optional[str]) -> Optional[str]:
        return _validar_telefono(v) if v is not None else None

    @field_validator("first_name", "last_name", "parent_name")
    @classmethod
    def validar_nombre(cls, v: Optional[str]) -> Optional[str]:
        return _validar_nombre(v) if v is not None else None

    def campos_a_actualizar(self) -> dict:
        """
        Devuelve solo los campos enviados por el cliente.

        Util en el controlador para construir el UPDATE sin sobreescribir
        con NULL los campos que el usuario no toco.
        """
        return self.model_dump(exclude_none=True)


class StudentResponse(BaseModel):
    """Estudiante tal como se devuelve al cliente. Nunca incluye password_hash."""

    id: int
    dni: str
    first_name: str
    last_name: str
    phone: str
    parent_name: str
    parent_phone: str