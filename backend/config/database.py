import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

# Usa directamente la variable DATABASE_URL del entorno
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    # Fallback para desarrollo local (si es necesario)
    "postgresql://postgres:postgres@localhost:5432/railway"
)

pool = None

# DEF-07: tiempo maximo de espera por una conexion libre del pool. Sin esto,
# `pool.acquire()` espera indefinidamente cuando las `max_size` conexiones
# estan ocupadas: bajo sobrecarga sostenida las peticiones se quedan colgadas
# en vez de fallar rapido con un 503 (ver tests/test_rendimiento.py, PRF-03).
ACQUIRE_TIMEOUT_SECONDS = 10

async def get_db_pool():
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=5,
            max_size=20,
            command_timeout=60,
            # Opciones adicionales para conexiones externas
            ssl="require" if "railway" in DATABASE_URL else "prefer"
        )
    return pool

async def close_db_pool():
    global pool
    if pool:
        await pool.close()
        pool = None

async def get_db():
    pool = await get_db_pool()
    async with pool.acquire(timeout=ACQUIRE_TIMEOUT_SECONDS) as connection:
        yield connection