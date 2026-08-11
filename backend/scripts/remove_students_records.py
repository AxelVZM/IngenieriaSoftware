# remove_students_records.py

"""
Script para eliminar matrículas, pagos y registros de estudiantes específicos
"""
import asyncio
import asyncpg
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

TARGET_STUDENTS = [
    ("Lucía", "Ruiz"),
    ("María", "Martínez"),
    ("Patricia", "Rivera"),
    ("Pedro", "Jiménez"),
    ("Raúl", "Castro"),
    ("Raúl", "Reyes"),
    ("Elena", "Chávez"),
    ("Javier", "Díaz"),
]

async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    print("✅ Conectado a la base de datos\n")
    
    try:
        total_deleted = 0
        for first_name, last_name in TARGET_STUDENTS:
            # 1. Buscar estudiante
            student = await conn.fetchrow("""
                SELECT id, first_name, last_name, dni FROM students
                WHERE first_name = $1 AND last_name = $2
            """, first_name, last_name)
            
            if not student:
                print(f"ℹ️ Estudiante no encontrado o ya eliminado: {first_name} {last_name}")
                continue
            
            student_id = student['id']
            dni = student['dni']
            
            # Ejecutar eliminación en orden de dependencia de claves foráneas
            async with conn.transaction():
                # Cuotas
                await conn.execute("""
                    DELETE FROM installments
                    WHERE payment_plan_id IN (
                        SELECT id FROM payment_plans
                        WHERE enrollment_id IN (SELECT id FROM enrollments WHERE student_id = $1)
                    )
                """, student_id)
                
                # Planes de pago
                await conn.execute("""
                    DELETE FROM payment_plans
                    WHERE enrollment_id IN (SELECT id FROM enrollments WHERE student_id = $1)
                """, student_id)
                
                # Matrículas
                await conn.execute("""
                    DELETE FROM enrollments WHERE student_id = $1
                """, student_id)
                
                # Asistencias
                await conn.execute("""
                    DELETE FROM attendance WHERE student_id = $1
                """, student_id)
                
                # Analytics Summary
                await conn.execute("""
                    DELETE FROM analytics_summary WHERE student_id = $1
                """, student_id)
                
                # Notifications Log
                await conn.execute("""
                    DELETE FROM notifications_log WHERE student_id = $1
                """, student_id)
                
                # Estudiante
                await conn.execute("""
                    DELETE FROM students WHERE id = $1
                """, student_id)
                
                # Usuario si existe
                await conn.execute("""
                    DELETE FROM users WHERE username = $1
                """, dni)
            
            total_deleted += 1
            print(f"🗑️ Eliminado correctamente: {first_name} {last_name} (DNI: {dni})")
        
        print(f"\n✅ Total eliminados en esta corrida: {total_deleted} estudiantes y todos sus registros relacionados.")

    except Exception as e:
        print(f"\n❌ Error al eliminar registros: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()
        print("\n🔌 Conexión cerrada")

if __name__ == "__main__":
    asyncio.run(main())
