"""
Middleware de autenticación — versión corregida.

  A-01  ESCALADA DE PRIVILEGIOS. En la versión anterior, si el token decía
        role="student" pero el estudiante ya no existía en la tabla
        `students`, la ejecución NO se detenía: caía al bloque siguiente y
        buscaba `SELECT ... FROM users WHERE id = $1` con el MISMO id.
        Como `students.id` y `users.id` son secuencias independientes,
        un token de estudiante con id=1 (dado de baja) devolvía el usuario
        users.id=1, que en la práctica suele ser el administrador creado
        por scripts/createAdmin.py. El resto de la aplicación pasaba a
        tratar esa sesión como admin.
        Ahora, si el token declara rol de estudiante, la búsqueda se limita
        a la tabla `students` y termina ahí.

  A-02  El rol del token no se contrastaba con el rol almacenado. Ahora se
        verifica que coincidan, de modo que un token manipulado o antiguo
        (usuario degradado de admin a docente) no conserva privilegios.

  A-03  Mensajes de error en inglés dentro de una aplicación en español.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.security import decode_token
from config.database import get_db
import asyncpg

security = HTTPBearer()

CREDENCIALES_INVALIDAS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Tu sesión no es válida o ha expirado. Inicia sesión nuevamente.",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: asyncpg.Connection = Depends(get_db),
):
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise CREDENCIALES_INVALIDAS

    user_id = payload.get("id")
    role = payload.get("role")

    if user_id is None or role is None:
        raise CREDENCIALES_INVALIDAS

    # ---- A-01: rama de estudiante, cerrada y sin caída al bloque de users ----
    if role == "student":
        student = await db.fetchrow(
            "SELECT id, dni, first_name, last_name FROM students WHERE id = $1",
            user_id,
        )
        if student is None:
            raise CREDENCIALES_INVALIDAS
        return {
            "id": student["id"],
            "username": student["dni"],
            "role": "student",
            "related_id": None,
            "first_name": student["first_name"],
            "last_name": student["last_name"],
        }

    # ---- Resto de roles ----
    user = await db.fetchrow(
        "SELECT id, username, role, related_id FROM users WHERE id = $1",
        user_id,
    )
    if user is None:
        raise CREDENCIALES_INVALIDAS

    # ---- A-02: el rol del token debe coincidir con el almacenado ----
    if user["role"] != role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tus permisos han cambiado. Vuelve a iniciar sesión.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return dict(user)


def require_role(allowed_roles: list):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para realizar esta acción.",
            )
        return current_user
    return role_checker