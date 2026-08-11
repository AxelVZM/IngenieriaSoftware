# enroll_students.py

"""
Script para matricular estudiantes en paquetes con pago verificado/aprobado
"""
import asyncio
import asyncpg
import random
from dotenv import load_dotenv
import os
import sys
from pathlib import Path
import cloudinary
import cloudinary.uploader
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Configurar Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

VOUCHER_PATH = r"C:\Users\Jacob\Downloads\images.jpg"

async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    print("✅ Conectado a la base de datos")
    
    try:
        # Obtener paquetes disponibles con ciclo activo
        packages = await conn.fetch("""
            SELECT po.id, p.name, po.price_override, p.base_price, po.cycle_id
            FROM package_offerings po
            JOIN packages p ON po.package_id = p.id
            JOIN cycles c ON po.cycle_id = c.id
            WHERE c.status = 'in_progress'
        """)
        
        if not packages:
            print("❌ No hay paquetes disponibles en ciclos activos")
            return
        
        print(f"📦 Encontrados {len(packages)} paquetes disponibles en ciclos activos")
        
        # Obtener estudiantes que NO tienen matrícula activa ni pendiente
        students = await conn.fetch("""
            SELECT s.id, s.first_name, s.last_name, s.dni
            FROM students s
            WHERE NOT EXISTS (
                SELECT 1 FROM enrollments e
                WHERE e.student_id = s.id
                  AND e.status IN ('pendiente', 'aceptado')
            )
            ORDER BY s.id
        """)
        
        if not students:
            print("ℹ️ Todos los estudiantes ya cuentan con matrícula activa o pendiente.")
            return
            
        print(f"👨‍🎓 Encontrados {len(students)} estudiantes disponibles para matricular")
        
        # Subir voucher a Cloudinary
        print(f"\n📤 Subiendo comprobante de pago a Cloudinary...")
        upload_result = cloudinary.uploader.upload(
            VOUCHER_PATH,
            folder="vouchers",
            resource_type="image"
        )
        voucher_url = upload_result['secure_url']
        print(f"✅ Comprobante subido: {voucher_url}\n")
        
        now = datetime.now()
        enrolled = 0
        
        for student in students:
            # Seleccionar paquete aleatorio
            package = random.choice(packages)
            price = package['price_override'] or package['base_price']
            
            # Verificar si ya existe matrícula para este estudiante y paquete específico
            existing = await conn.fetchrow("""
                SELECT id FROM enrollments
                WHERE student_id = $1 AND package_offering_id = $2 AND status != 'cancelado'
            """, student['id'], package['id'])
            
            if existing:
                continue
            
            # Transacción atómica por matrícula
            async with conn.transaction():
                # 1. Crear matrícula principal del paquete como 'aceptado'
                enrollment = await conn.fetchrow("""
                    INSERT INTO enrollments (student_id, package_offering_id, enrollment_type, status, registered_at, accepted_at)
                    VALUES ($1, $2, 'package', 'aceptado', $3, $3)
                    RETURNING id
                """, student['id'], package['id'], now)
                
                # 2. Crear plan de pago
                payment_plan = await conn.fetchrow("""
                    INSERT INTO payment_plans (enrollment_id, total_amount, installments)
                    VALUES ($1, $2, 1)
                    RETURNING id
                """, enrollment['id'], price)
                
                # 3. Crear cuota como 'paid' con voucher y fecha de pago
                due_date = now + timedelta(days=7)
                await conn.execute("""
                    INSERT INTO installments (payment_plan_id, installment_number, amount, due_date, status, voucher_url, paid_at)
                    VALUES ($1, 1, $2, $3, 'paid', $4, $5)
                """, payment_plan['id'], price, due_date.date(), voucher_url, now)
                
                # 4. Vincular los cursos del paquete al estudiante en enrollments
                ofertas_cursos = await conn.fetch("""
                    SELECT course_offering_id FROM package_offering_courses
                    WHERE package_offering_id = $1
                """, package['id'])
                
                for oferta in ofertas_cursos:
                    await conn.execute("""
                        INSERT INTO enrollments
                          (student_id, course_offering_id, package_offering_id,
                           enrollment_type, status, registered_at, accepted_at)
                        VALUES ($1, $2, $3, 'course', 'aceptado', $4, $4)
                        ON CONFLICT DO NOTHING
                    """, student['id'], oferta['course_offering_id'], package['id'], now)
            
            enrolled += 1
            print(f"  ✓ {student['first_name']} {student['last_name']} → {package['name']} (S/ {price}) [PAGADO Y ACEPTADO]")
        
        print(f"\n✅ {enrolled} estudiantes matriculados exitosamente con pago verificado!")
        print(f"📊 Estado en sistema: 'Aceptado' / Pago 'Pagado'")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()
        print("\n🔌 Conexión cerrada")

if __name__ == "__main__":
    asyncio.run(main())
