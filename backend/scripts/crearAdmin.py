import asyncio
import asyncpg
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.security import get_password_hash
from dotenv import load_dotenv

load_dotenv()

async def create_admin():
    try:
        DATABASE_URL = os.getenv("DATABASE_URL")
        conn = await asyncpg.connect(DATABASE_URL)
        
        password = "admin123"
        password_hash = get_password_hash(password)
        
        await conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES ($1, $2, $3)",
            "admin", password_hash, "admin"
        )
        
        print("Usuario administrador creado exitosamente")
        print("Username: admin")
        print("Password: admin123")
        
        await conn.close()
    except asyncpg.UniqueViolationError:
        print("El usuario administrador ya existe")
    except Exception as e:
        print(f"Error al crear el administrador: {e}")

if __name__ == "__main__":
    asyncio.run(create_admin())