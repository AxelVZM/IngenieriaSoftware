
from __future__ import annotations

import logging

import asyncpg

from models.student import StudentCreate
from models.user import UserLogin
from utils.errors import (
    DB_UNAVAILABLE_MESSAGE,
    GENERIC_CREDENTIALS_MESSAGE,
    GENERIC_SERVER_MESSAGE,
    api_error,
)
from utils.rate_limit import build_attempt_key, login_attempts
from utils.security import (
    create_access_token,
    fake_verify_password,
    get_password_hash,
    verify_password,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Registro
# ---------------------------------------------------------------------------


async def register_student(data: StudentCreate, db: asyncpg.Connection) -> dict:
    """
    Registra un nuevo estudiante.

    La validacion de formato (DNI, telefonos, contrasena) ya la hizo Pydantic
    en StudentCreate, por lo que aqui solo se controla la unicidad y los
    errores de infraestructura.
    """
    try:
        existing = await db.fetchrow(
            "SELECT id FROM students WHERE dni = $1", data.dni
        )
        if existing:
            raise api_error(
                409,
                "DNI_ALREADY_REGISTERED",
                "Este DNI ya se encuentra registrado. Inicia sesion o usa otro DNI.",
            )

        password_hash = get_password_hash(data.password)

        result = await db.fetchrow(
            """INSERT INTO students
                   (dni, first_name, last_name, phone,
                    parent_name, parent_phone, password_hash)
               VALUES ($1, $2, $3, $4, $5, $6, $7)
               RETURNING id""",
            data.dni,
            data.first_name,
            data.last_name,
            data.phone,
            data.parent_name,
            data.parent_phone,
            password_hash,
        )

        if result is None:
            logger.error("El INSERT de estudiante no devolvio id (dni=%s)", data.dni)
            raise api_error(500, "REGISTRATION_FAILED", GENERIC_SERVER_MESSAGE)

        token = create_access_token({"id": result["id"], "role": "student"})

        return {
            "token": token,
            "user": {
                "id": result["id"],
                "dni": data.dni,
                "role": "student",
                "first_name": data.first_name,
                "last_name": data.last_name,
            },
        }

    except asyncpg.exceptions.UniqueViolationError:
        # Condicion de carrera: otro registro con el mismo DNI entro primero.
        raise api_error(
            409,
            "DNI_ALREADY_REGISTERED",
            "Este DNI ya se encuentra registrado. Inicia sesion o usa otro DNI.",
        )
    except asyncpg.PostgresError:
        logger.exception("Error de base de datos durante el registro")
        raise api_error(503, "DB_UNAVAILABLE", DB_UNAVAILABLE_MESSAGE)


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


async def _fetch_account(db: asyncpg.Connection, identifier: str) -> tuple[dict | None, str]:
    """
    Busca la cuenta primero en `users` (admin/docente) y luego en `students`.

    Returns:
        (registro, origen) donde origen es "users", "students" o "".
    """
    user = await db.fetchrow(
        "SELECT id, username, role, password_hash, related_id "
        "FROM users WHERE username = $1",
        identifier,
    )
    if user:
        return dict(user), "users"

    student = await db.fetchrow(
        "SELECT id, dni, first_name, last_name, password_hash "
        "FROM students WHERE dni = $1",
        identifier,
    )
    if student:
        return dict(student), "students"

    return None, ""


async def login_user(
    credentials: UserLogin,
    db: asyncpg.Connection,
    client_ip: str = "unknown",
) -> dict:
    """
    Autentica a un usuario (admin, docente o estudiante).

    Ante credenciales incorrectas devuelve SIEMPRE el mismo mensaje y el
    mismo codigo, exista o no el DNI en el sistema.
    """
    identifier = credentials.dni.strip()
    attempt_key = build_attempt_key(identifier, client_ip)

    # 1) Bloqueo por exceso de intentos fallidos
    bloqueado = login_attempts.seconds_blocked(attempt_key)
    if bloqueado:
        minutos = max(1, bloqueado // 60)
        raise api_error(
            429,
            "TOO_MANY_ATTEMPTS",
            f"Demasiados intentos fallidos. Vuelve a intentarlo en {minutos} minuto(s).",
            headers={"Retry-After": str(bloqueado)},
        )

    # 2) Busqueda de la cuenta
    try:
        account, origen = await _fetch_account(db, identifier)
    except asyncpg.PostgresError:
        logger.exception("Error de base de datos durante el login")
        raise api_error(503, "DB_UNAVAILABLE", DB_UNAVAILABLE_MESSAGE)

    # 3) Verificacion de contrasena (con defensa contra timing attacks)
    if account is None:
        fake_verify_password(credentials.password)
        login_attempts.register_failure(attempt_key)
        raise api_error(401, "INVALID_CREDENTIALS", GENERIC_CREDENTIALS_MESSAGE)

    if not verify_password(credentials.password, account.get("password_hash")):
        login_attempts.register_failure(attempt_key)
        raise api_error(401, "INVALID_CREDENTIALS", GENERIC_CREDENTIALS_MESSAGE)

    login_attempts.reset(attempt_key)

    # 4) Construccion de la respuesta segun el origen de la cuenta
    try:
        if origen == "users":
            user_data = {
                "id": account["id"],
                "username": account["username"],
                "role": account["role"],
            }

            if account["role"] == "teacher" and account.get("related_id"):
                teacher = await db.fetchrow(
                    "SELECT first_name, last_name, email FROM teachers WHERE id = $1",
                    account["related_id"],
                )
                if teacher:
                    user_data["name"] = f"{teacher['first_name']} {teacher['last_name']}"
                    user_data["email"] = teacher["email"]
                    user_data["related_id"] = account["related_id"]

            token = create_access_token(
                {"id": account["id"], "role": account["role"]}
            )
            return {"token": token, "user": user_data}

        # origen == "students"
        token = create_access_token({"id": account["id"], "role": "student"})
        return {
            "token": token,
            "user": {
                "id": account["id"],
                "dni": account["dni"],
                "role": "student",
                "name": f"{account['first_name']} {account['last_name']}",
            },
        }

    except asyncpg.PostgresError:
        logger.exception("Error de base de datos al armar la respuesta de login")
        raise api_error(503, "DB_UNAVAILABLE", DB_UNAVAILABLE_MESSAGE)