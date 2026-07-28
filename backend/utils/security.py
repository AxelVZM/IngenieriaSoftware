

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
load_dotenv()

# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------

ALGORITHM = "HS256"
MIN_SECRET_LENGTH = 32
BCRYPT_MAX_BYTES = 72  # limite propio del algoritmo bcrypt

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", str(12 * 60)))

_INSECURE_SECRETS = {
    "your-secret-key-here",
    "your_jwt_secret_here",
    "secret",
    "changeme",
    "123456",
}

SECRET_KEY = os.getenv("JWT_SECRET")

if not SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET no esta definido en las variables de entorno.\n"
        "Genera una clave segura con:\n"
        '  python -c "import secrets; print(secrets.token_urlsafe(64))"'
    )

if SECRET_KEY.strip().lower() in _INSECURE_SECRETS:
    raise RuntimeError(
        "JWT_SECRET tiene un valor de ejemplo inseguro. Genera una clave real "
        'con: python -c "import secrets; print(secrets.token_urlsafe(64))"'
    )

if len(SECRET_KEY) < MIN_SECRET_LENGTH:
    raise RuntimeError(
        f"JWT_SECRET es demasiado corto ({len(SECRET_KEY)} caracteres). "
        f"Se requieren al menos {MIN_SECRET_LENGTH}."
    )

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash senuelo: se usa para que un login con DNI inexistente consuma
# aproximadamente el mismo tiempo que uno con DNI valido. Evita que un
# atacante deduzca que DNIs existen midiendo el tiempo de respuesta.
_DUMMY_HASH = pwd_context.hash("timing-defense-placeholder-value")


# ---------------------------------------------------------------------------
# Excepciones de token
# ---------------------------------------------------------------------------


class TokenError(Exception):
    """Error base al procesar un token JWT."""


class TokenExpiredError(TokenError):
    """El token es valido pero su fecha de expiracion ya paso."""


class TokenInvalidError(TokenError):
    """El token esta mal formado, mal firmado o le faltan claims."""


# ---------------------------------------------------------------------------
# Contrasenas
# ---------------------------------------------------------------------------


def _truncate_for_bcrypt(password: str) -> str:
    """Recorta la contrasena al limite de 72 bytes que impone bcrypt."""
    encoded = password.encode("utf-8")
    if len(encoded) <= BCRYPT_MAX_BYTES:
        return password
    return encoded[:BCRYPT_MAX_BYTES].decode("utf-8", errors="ignore")


def get_password_hash(password: str) -> str:
    """Devuelve el hash bcrypt de una contrasena en texto plano."""
    return pwd_context.hash(_truncate_for_bcrypt(password))


def verify_password(plain_password: str, hashed_password: Optional[str]) -> bool:
    """
    Compara una contrasena en texto plano contra su hash almacenado.

    Devuelve False (nunca lanza excepcion) si el hash es nulo o esta corrupto,
    para que el controlador siempre pueda responder un 401 controlado.
    """
    if not hashed_password:
        return False
    try:
        return pwd_context.verify(_truncate_for_bcrypt(plain_password), hashed_password)
    except Exception:
        return False


def fake_verify_password(plain_password: str) -> None:
    """
    Ejecuta una verificacion contra un hash senuelo.

    No devuelve nada util: su unico proposito es consumir el mismo tiempo de
    CPU que una verificacion real cuando el usuario no existe.
    """
    try:
        pwd_context.verify(_truncate_for_bcrypt(plain_password), _DUMMY_HASH)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Tokens JWT
# ---------------------------------------------------------------------------


def create_access_token(
    data: dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Genera un token JWT firmado.

    Args:
        data: claims a incluir (normalmente {"id": int, "role": str}).
        expires_delta: duracion personalizada. Si se omite se usa
            ACCESS_TOKEN_EXPIRE_MINUTES.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": now})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decodifica y valida un token JWT.

    Raises:
        TokenExpiredError: si el token expiro.
        TokenInvalidError: si la firma es invalida, el token esta mal formado
            o faltan los claims obligatorios (id, role).
    """
    if not token:
        raise TokenInvalidError("Token vacio")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError as exc:
        raise TokenExpiredError("El token ha expirado") from exc
    except JWTError as exc:
        raise TokenInvalidError("Token invalido") from exc

    if payload.get("id") is None or not payload.get("role"):
        raise TokenInvalidError("El token no contiene los datos requeridos")

    return payload