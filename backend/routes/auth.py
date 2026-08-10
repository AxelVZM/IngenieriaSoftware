"""Rutas de autenticacion."""

from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends, Request, status

import controllers.authController as authController
from config.database import get_db
from models.student import StudentCreate
from models.user import UserLogin

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str:
    """
    Obtiene la IP real del cliente.

    Detras de un proxy (Railway, Nginx) la IP directa es la del proxy, por eso
    se prioriza la primera entrada de X-Forwarded-For.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user: StudentCreate,
    db: asyncpg.Connection = Depends(get_db),
):
    """Registro de estudiantes. Los errores se lanzan desde el controlador."""
    return await authController.register_student(user, db)


@router.post("/login")
async def login(
    credentials: UserLogin,
    request: Request,
    db: asyncpg.Connection = Depends(get_db),
):
    """Inicio de sesion para admin, docente y estudiante."""
    return await authController.login_user(credentials, db, _client_ip(request))