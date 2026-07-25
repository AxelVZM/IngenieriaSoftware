"""
Script para aceptar todas las matrículas pendientes y aprobar pagos
"""
import asyncio
import asyncpg
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    print("✅ Conectado a la base de datos")
    
    try:
        # Obtener matrículas pendientes
        enrollments = await conn.fetch("""
            SELECT e.id, s.first_name, s.last_name, e.enrollment_type
            FROM enrollments e
            JOIN students s ON e.student_id = s.id
            WHERE e.status = 'pendiente'
        """)
        
        print(f"\n📋 Encontradas {len(enrollments)} matrículas pendientes")
        
        accepted = 0
        for enrollment in enrollments:
            # Aceptar matrícula
            await conn.execute("""
                UPDATE enrollments
                SET status = 'aceptado', accepted_at = $1
                WHERE id = $2
            """, datetime.now(), enrollment['id'])
            
            # Aprobar pago (marcar cuota como pagada)
            await conn.execute("""
                UPDATE installments i
                SET status = 'paid', paid_at = $1
                FROM payment_plans pp
                WHERE i.payment_plan_id = pp.id
                AND pp.enrollment_id = $2
            """, datetime.now(), enrollment['id'])
            
            accepted += 1
            print(f"  ✓ {enrollment['first_name']} {enrollment['last_name']} - {enrollment['enrollment_type']}")
        
        print(f"\n✅ {accepted} matrículas aceptadas y pagos aprobados!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()
        print("\n🔌 Conexión cerrada")

if __name__ == "__main__":
    asyncio.run(main())
