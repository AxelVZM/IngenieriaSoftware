# create_students.py

"""
Script para crear 20+ estudiantes de prueba
Usa bcrypt para hashear contraseñas (mismo método que el sistema)
"""
import asyncio
import asyncpg
import random
from dotenv import load_dotenv
import os
import bcrypt

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Datos base
NOMBRES = [
    "Juan", "María", "Pedro", "Ana", "Luis", "Carmen", "Carlos", "Rosa",
    "Miguel", "Laura", "José", "Isabel", "Antonio", "Sofía", "Francisco",
    "Elena", "Javier", "Patricia", "Manuel", "Lucía", "Raúl", "Marta",
    "Diego", "Cristina", "Alberto", "Beatriz", "Fernando", "Gloria",
    "Roberto", "Teresa"
]

APELLIDOS = [
    "García", "Rodríguez", "Martínez", "López", "González", "Pérez",
    "Sánchez", "Ramírez", "Torres", "Flores", "Rivera", "Gómez",
    "Díaz", "Cruz", "Morales", "Reyes", "Ortiz", "Gutiérrez",
    "Chávez", "Ruiz", "Jiménez", "Hernández", "Mendoza", "Vargas",
    "Castro", "Romero", "Ramos", "Medina", "Navarro", "Campos"
]

PHONES = ["969728039", "956399615", "985121933", "952873813"]

async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    print("✅ Conectado a la base de datos")
    
    try:
        num_students = 5
        print(f"\n👨‍🎓 Creando {num_students} estudiantes...")
        
        created = 0
        for i in range(num_students):
            nombre = random.choice(NOMBRES)
            apellido = random.choice(APELLIDOS)
            dni = f"{random.randint(10000000, 99999999)}"
            phone = random.choice(PHONES)
            parent_name = f"{random.choice(NOMBRES)} {random.choice(APELLIDOS)}"
            
            # Verificar si ya existe el DNI
            existing = await conn.fetchval("SELECT id FROM students WHERE dni = $1", dni)
            if existing:
                continue
            
            # Password hasheado (default: 123456)
            password = "A123456"
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            student = await conn.fetchrow(
                """INSERT INTO students (dni, first_name, last_name, phone, parent_name, parent_phone, password_hash)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)
                   RETURNING id, dni, first_name, last_name""",
                dni, nombre, apellido, phone, parent_name, phone, password_hash
            )
            
            created += 1
            print(f"  ✓ {student['first_name']} {student['last_name']} - DNI: {student['dni']} - Pass: {password}")
        
        print(f"\n✅ {created} estudiantes creados exitosamente!")
        print(f"\n📝 Contraseñas: A123456 para todos")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()
        print("\n🔌 Conexión cerrada")

if __name__ == "__main__":
    asyncio.run(main())
