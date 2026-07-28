"""
Utilidades de seguridad del sistema de autenticacion.

Contiene:
  - Hashing y verificacion de contrasenas (biblioteca bcrypt directa).
  - Generacion y decodificacion de tokens JWT.
  - Defensa basica contra ataques de temporizacion (timing attacks).

IMPORTANTE: este modulo hace *fail-fast*. Si JWT_SECRET no esta definido,
es demasiado corto o es un valor de ejemplo conocido, la aplicacion NO
arranca. Esto elimina el riesgo de firmar tokens con una clave por defecto.
"""

# NOTA: 'from __future__' debe ser la primera sentencia del archivo; solo el
# docstring y los comentarios pueden ir por encima. No mover esta linea.
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from dotenv import load_dotenv
import bcrypt
from jose import ExpiredSignatureError, JWTError, jwt

# Este modulo se importa muy temprano (routes -> middleware -> security), a
# veces antes que config.database, que es donde vivia el unico load_dotenv().
# Lo llamamos aqui para no depender del orden de los imports. load_dotenv()
# es idempotente: invocarlo dos veces no causa ningun problema.
load_dotenv()

# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------

ALGORITHM = "HS256"
MIN_SECRET_LENGTH = 32
BCRYPT_MAX_BYTES = 72  # limite propio del algoritmo bcrypt
BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))

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
        '  python -c "import secrets; print(secrets.token_urlsafe(64))"\n'
        "y guardala en el archivo backend/.env como JWT_SECRET=..."
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

# Hash senuelo: se usa para que un login con DNI inexistente consuma
# aproximadamente el mismo tiempo que uno con DNI valido. Evita que un
# atacante deduzca que DNIs existen midiendo el tiempo de respuesta.
_DUMMY_HASH = bcrypt.hashpw(
    b"timing-defense-placeholder-value", bcrypt.gensalt(BCRYPT_ROUNDS)
)


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


def _a_bytes(password: str) -> bytes:
    """
    Convierte la contrasena a bytes y la recorta al limite de bcrypt.

    El recorte es explicito y no delegado: las versiones de bcrypt anteriores
    a la 4.1 truncaban en silencio, mientras que las posteriores lanzan
    ValueError. Al recortar aqui, el comportamiento es identico en todas.
    """
    return password.encode("utf-8")[:BCRYPT_MAX_BYTES]


def get_password_hash(password: str) -> str:
    """Devuelve el hash bcrypt de una contrasena en texto plano."""
    return bcrypt.hashpw(_a_bytes(password), bcrypt.gensalt(BCRYPT_ROUNDS)).decode()


def verify_password(plain_password: str, hashed_password: Optional[str]) -> bool:
    """
    Compara una contrasena en texto plano contra su hash almacenado.

    Devuelve False (nunca lanza excepcion) si el hash es nulo o esta corrupto,
    para que el controlador siempre pueda responder un 401 controlado.

    Verifica sin problema los hashes creados anteriormente con passlib: ambos
    producen el mismo formato estandar $2b$.
    """
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(_a_bytes(plain_password), hashed_password.encode())
    except Exception:
        return False


def fake_verify_password(plain_password: str) -> None:
    """
    Ejecuta una verificacion contra un hash senuelo.

    No devuelve nada util: su unico proposito es consumir el mismo tiempo de
    CPU que una verificacion real cuando el usuario no existe.
    """
    try:
        bcrypt.checkpw(_a_bytes(plain_password), _DUMMY_HASH)
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