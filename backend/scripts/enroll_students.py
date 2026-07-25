"""
Script para matricular estudiantes en paquetes y subir comprobante de pago
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

VOUCHER_PATH = r"C:\Users\Jacobo\Downloads\images.jpg"

async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    print("✅ Conectado a la base de datos")
    
    try:
        # Obtener todos los estudiantes
        students = await conn.fetch("SELECT id, first_name, last_name, dni FROM students ORDER BY id")
        print(f"\n👨‍🎓 Encontrados {len(students)} estudiantes")
        
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
        
        print(f"📦 Encontrados {len(packages)} paquetes disponibles")
        
        # Subir voucher a Cloudinary
        print(f"\n📤 Subiendo comprobante de pago...")
        upload_result = cloudinary.uploader.upload(
            VOUCHER_PATH,
            folder="vouchers",
            resource_type="image"
        )
        voucher_url = upload_result['secure_url']
        print(f"✅ Comprobante subido: {voucher_url}")
        
        enrolled = 0
        for student in students:
            # Seleccionar paquete aleatorio
            package = random.choice(packages)
            price = package['price_override'] or package['base_price']
            
            # Crear matrícula
            enrollment = await conn.fetchrow("""
                INSERT INTO enrollments (student_id, package_offering_id, enrollment_type, status)
                VALUES ($1, $2, 'package', 'pendiente')
                RETURNING id
            """, student['id'], package['id'])
            
            # Crear plan de pago
            payment_plan = await conn.fetchrow("""
                INSERT INTO payment_plans (enrollment_id, total_amount, installments)
                VALUES ($1, $2, 1)
                RETURNING id
            """, enrollment['id'], price)
            
            # Crear cuota con voucher
            due_date = datetime.now() + timedelta(days=7)
            await conn.execute("""
                INSERT INTO installments (payment_plan_id, installment_number, amount, due_date, status, voucher_url)
                VALUES ($1, 1, $2, $3, 'pending', $4)
            """, payment_plan['id'], price, due_date.date(), voucher_url)
            
            enrolled += 1
            print(f"  ✓ {student['first_name']} {student['last_name']} → {package['name']} (S/ {price})")
        
        print(f"\n✅ {enrolled} estudiantes matriculados exitosamente!")
        print(f"📝 Todos tienen comprobante de pago pendiente de revisión")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()
        print("\n🔌 Conexión cerrada")

if __name__ == "__main__":
    asyncio.run(main())
