
from __future__ import annotations

import logging

import asyncpg
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config.database import get_db
from utils.errors import DB_UNAVAILABLE_MESSAGE, api_error
from utils.security import TokenExpiredError, TokenInvalidError, decode_token

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

_WWW_AUTH = {"WWW-Authenticate": "Bearer"}


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: asyncpg.Connection = Depends(get_db),
) -> dict:
    """
    Valida el token Bearer y devuelve el usuario autenticado.

    Distingue explicitamente:
      - TOKEN_MISSING  (401): no se envio cabecera Authorization.
      - TOKEN_EXPIRED  (401): el token caduco -> el frontend debe cerrar sesion.
      - TOKEN_INVALID  (401): firma incorrecta o token mal formado.
      - USER_NOT_FOUND (401): el token es valido pero la cuenta ya no existe.
    """
    if credentials is None or not credentials.credentials:
        raise api_error(
            401, "TOKEN_MISSING", "Sesion no iniciada.", headers=_WWW_AUTH
        )

    try:
        payload = decode_token(credentials.credentials)
    except TokenExpiredError:
        raise api_error(
            401,
            "TOKEN_EXPIRED",
            "Tu sesion ha expirado. Inicia sesion nuevamente.",
            headers=_WWW_AUTH,
        )
    except TokenInvalidError:
        raise api_error(
            401, "TOKEN_INVALID", "Sesion invalida.", headers=_WWW_AUTH
        )

    user_id = payload["id"]
    role = payload["role"]

    try:
        if role == "student":
            student = await db.fetchrow(
                "SELECT id, dni FROM students WHERE id = $1", user_id
            )
            if student:
                return {
                    "id": student["id"],
                    "username": student["dni"],
                    "role": "student",
                    "related_id": None,
                }
            # Si el rol dice student pero no existe, no se sigue buscando en
            # users: eso permitiria escalar privilegios con un id coincidente.
            raise api_error(
                401, "USER_NOT_FOUND", "La cuenta ya no existe.", headers=_WWW_AUTH
            )

        user = await db.fetchrow(
            "SELECT id, username, role, related_id FROM users WHERE id = $1",
            user_id,
        )
    except asyncpg.PostgresError:
        logger.exception("Error de base de datos al validar el token")
        raise api_error(503, "DB_UNAVAILABLE", DB_UNAVAILABLE_MESSAGE)

    if user is None:
        raise api_error(
            401, "USER_NOT_FOUND", "La cuenta ya no existe.", headers=_WWW_AUTH
        )

    # El rol autoritativo es el de la base de datos, no el del token: si a un
    # usuario le cambian el rol, el token viejo no conserva permisos antiguos.
    if user["role"] != role:
        raise api_error(
            401,
            "TOKEN_INVALID",
            "Tu sesion ya no es valida. Inicia sesion nuevamente.",
            headers=_WWW_AUTH,
        )

    return dict(user)


def require_role(allowed_roles: list[str]):
    """
    Dependencia que exige uno de los roles indicados.

    Uso:
        @router.get("/admin/algo")
        async def handler(user = Depends(require_role(["admin"]))):
            ...
    """

    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in allowed_roles:
            raise api_error(
                403,
                "FORBIDDEN",
                "No tienes permisos para realizar esta accion.",
            )
        return current_user

    return role_checker