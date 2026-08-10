
from __future__ import annotations

from typing import Optional

from fastapi import HTTPException


def api_error(
    status_code: int,
    code: str,
    message: str,
    headers: Optional[dict] = None,
) -> HTTPException:
    """
    Construye una HTTPException con el formato estandar del proyecto.

    Uso:
        raise api_error(401, "INVALID_CREDENTIALS", "DNI o contrasena incorrectos.")
    """
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message},
        headers=headers,
    )


# Mensajes reutilizados: se centralizan para que no existan variantes que
# revelen informacion distinta segun el caso (enumeracion de usuarios).
GENERIC_CREDENTIALS_MESSAGE = "DNI o contraseña incorrectos. Inténtalo de nuevo."
GENERIC_SERVER_MESSAGE = (
    "Ocurrió un error inesperado. Inténtalo nuevamente en unos momentos."
)
DB_UNAVAILABLE_MESSAGE = (
    "El servicio no está disponible temporalmente. Inténtalo más tarde."
)