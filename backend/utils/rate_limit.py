"""
Control de intentos fallidos de autenticacion.

Implementa un bloqueo temporal por combinacion (identificador + IP) para
mitigar ataques de fuerza bruta contra el endpoint de login.

LIMITACION CONOCIDA: el contador vive en memoria del proceso. Si se levanta
la API con varios workers (uvicorn --workers N) o varias instancias, cada
proceso llevara su propio conteo. Para produccion real conviene mover este
estado a Redis o a una tabla `login_attempts` en PostgreSQL; la interfaz
publica de esta clase se mantendria igual.
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass

MAX_ATTEMPTS = int(os.getenv("LOGIN_MAX_ATTEMPTS", "5"))
WINDOW_SECONDS = int(os.getenv("LOGIN_WINDOW_SECONDS", "900"))  # 15 min
BLOCK_SECONDS = int(os.getenv("LOGIN_BLOCK_SECONDS", "900"))  # 15 min


@dataclass
class _Entry:
    failures: int = 0
    first_failure_at: float = 0.0
    blocked_until: float = 0.0


class LoginAttemptTracker:
    """Registra intentos fallidos y determina si una clave esta bloqueada."""

    def __init__(
        self,
        max_attempts: int = MAX_ATTEMPTS,
        window_seconds: int = WINDOW_SECONDS,
        block_seconds: int = BLOCK_SECONDS,
    ) -> None:
        self._max_attempts = max_attempts
        self._window = window_seconds
        self._block = block_seconds
        self._data: dict[str, _Entry] = {}
        self._lock = threading.Lock()
        self._last_cleanup = time.monotonic()

    # -- API publica --------------------------------------------------------

    def seconds_blocked(self, key: str) -> int:
        """
        Devuelve cuantos segundos falta para desbloquear la clave.
        Devuelve 0 si no esta bloqueada.
        """
        now = time.monotonic()
        with self._lock:
            self._cleanup(now)
            entry = self._data.get(key)
            if entry is None or entry.blocked_until <= now:
                return 0
            return int(entry.blocked_until - now) + 1

    def register_failure(self, key: str) -> int:
        """
        Registra un intento fallido. Devuelve los intentos restantes antes
        del bloqueo (0 si se acaba de bloquear).
        """
        now = time.monotonic()
        with self._lock:
            self._cleanup(now)
            entry = self._data.setdefault(key, _Entry())

            # La ventana de conteo caduco: se reinicia el contador.
            if entry.first_failure_at and (now - entry.first_failure_at) > self._window:
                entry.failures = 0
                entry.first_failure_at = 0.0

            if entry.failures == 0:
                entry.first_failure_at = now

            entry.failures += 1

            if entry.failures >= self._max_attempts:
                entry.blocked_until = now + self._block
                entry.failures = 0
                entry.first_failure_at = 0.0
                return 0

            return self._max_attempts - entry.failures

    def reset(self, key: str) -> None:
        """Limpia el historial de una clave tras un login exitoso."""
        with self._lock:
            self._data.pop(key, None)

    # -- Interno ------------------------------------------------------------

    def _cleanup(self, now: float) -> None:
        """Elimina entradas caducadas cada 5 minutos para no crecer sin limite."""
        if now - self._last_cleanup < 300:
            return
        self._last_cleanup = now
        expired = [
            k
            for k, e in self._data.items()
            if e.blocked_until <= now
            and (not e.first_failure_at or (now - e.first_failure_at) > self._window)
        ]
        for k in expired:
            self._data.pop(k, None)


# Instancia compartida por toda la aplicacion.
login_attempts = LoginAttemptTracker()


def build_attempt_key(identifier: str, client_ip: str) -> str:
    """Construye la clave de conteo: identificador normalizado + IP origen."""
    return f"{(identifier or '').strip().lower()}|{client_ip or 'unknown'}"