# clear_db.py

"""
Script para borrar TODOS los datos de la base de datos
Usa TRUNCATE CASCADE para eliminar todo de forma directa
"""
import asyncio
import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Todas las tablas de la base de datos
TABLES = [
    "users",
    "teachers", 
    "students",
    "cycles",
    "courses",
    "packages",
    "package_courses",
    "course_offerings",
    "package_offerings",
    "schedules",
    "enrollments",
    "payment_plans",
    "installments",
    "attendance",
    "notifications_log",
    "analytics_summary",
    "package_offering_courses"
]

async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    print("✅ Conectado a la base de datos")
    
    try:
        print("\n🗑️  Borrando TODOS los datos con TRUNCATE CASCADE...")
        
        # TRUNCATE CASCADE borra todo y resetea auto-increment
        tables_str = ", ".join(TABLES)
        await conn.execute(f"TRUNCATE TABLE {tables_str} RESTART IDENTITY CASCADE")
        
        print(f"  ✓ {len(TABLES)} tablas limpiadas")
        
        print("\n✅ ¡Todos los datos eliminados exitosamente!")
        
        # Verificación
        print("\n📊 Verificación (todos deberían ser 0):")
        for table in TABLES:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            print(f"  • {table}: {count}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()
        print("\n🔌 Conexión cerrada")

if __name__ == "__main__":
    asyncio.run(main())
