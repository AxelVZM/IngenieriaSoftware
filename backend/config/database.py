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
    async with pool.acquire() as connection:
        yield connection