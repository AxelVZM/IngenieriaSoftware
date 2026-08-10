# verify_teachers.py

"""
Script para verificar la relación entre docentes y estudiantes
Muestra cuántos estudiantes tiene cada docente según las matrículas aceptadas
"""
import asyncio
import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    print("✅ Conectado a la base de datos\n")
    
    try:
        # Query para obtener docentes con sus estudiantes (incluyendo paquetes)
        results = await conn.fetch("""
            SELECT 
                t.id as teacher_id,
                t.first_name || ' ' || t.last_name as teacher_name,
                COUNT(DISTINCT e.student_id) as total_students,
                STRING_AGG(DISTINCT s.first_name || ' ' || s.last_name, ', ') as students
            FROM teachers t
            LEFT JOIN course_offerings co ON t.id = co.teacher_id
            LEFT JOIN enrollments e ON co.id = e.course_offering_id AND e.status = 'aceptado'
            LEFT JOIN package_offering_courses poc ON co.id = poc.course_offering_id
            LEFT JOIN package_offerings po ON poc.package_offering_id = po.id
            LEFT JOIN enrollments e2 ON po.id = e2.package_offering_id AND e2.status = 'aceptado'
            LEFT JOIN students s ON (e.student_id = s.id OR e2.student_id = s.id)
            GROUP BY t.id, t.first_name, t.last_name
            ORDER BY total_students DESC, t.last_name
        """)
        
        print("=" * 80)
        print("DOCENTES Y SUS ESTUDIANTES")
        print("=" * 80)
        
        for row in results:
            print(f"\n👨‍🏫 {row['teacher_name']} (ID: {row['teacher_id']})")
            print(f"   Total estudiantes: {row['total_students']}")
            if row['students']:
                print(f"   Estudiantes: {row['students'][:100]}{'...' if len(row['students']) > 100 else ''}")
            else:
                print(f"   ⚠️  Sin estudiantes asignados")
        
        print("\n" + "=" * 80)
        
        # Resumen
        with_students = sum(1 for r in results if r['total_students'] > 0)
        without_students = sum(1 for r in results if r['total_students'] == 0)
        
        print(f"\n📊 RESUMEN:")
        print(f"   Docentes con estudiantes: {with_students}")
        print(f"   Docentes sin estudiantes: {without_students}")
        print(f"   Total docentes: {len(results)}")
        
        # Verificar matrículas en paquetes
        print("\n" + "=" * 80)
        print("VERIFICANDO MATRÍCULAS EN PAQUETES...")
        print("=" * 80)
        
        package_enrollments = await conn.fetch("""
            SELECT 
                po.id as package_offering_id,
                p.name as package_name,
                COUNT(DISTINCT e.student_id) as students_enrolled
            FROM package_offerings po
            JOIN packages p ON po.package_id = p.id
            LEFT JOIN enrollments e ON po.id = e.package_offering_id AND e.status = 'aceptado'
            GROUP BY po.id, p.name
            HAVING COUNT(DISTINCT e.student_id) > 0
            ORDER BY students_enrolled DESC
        """)
        
        for row in package_enrollments:
            print(f"\n📦 {row['package_name']}")
            print(f"   Estudiantes matriculados: {row['students_enrolled']}")
        
        # Verificar cursos dentro de paquetes
        print("\n" + "=" * 80)
        print("VERIFICANDO CURSOS DENTRO DE PAQUETES CON DOCENTES...")
        print("=" * 80)
        
        package_courses = await conn.fetch("""
            SELECT 
                p.name as package_name,
                c.name as course_name,
                t.first_name || ' ' || t.last_name as teacher_name,
                COUNT(DISTINCT e.student_id) as students_in_package
            FROM package_offerings po
            JOIN packages p ON po.package_id = p.id
            JOIN package_offering_courses poc ON po.id = poc.package_offering_id
            JOIN course_offerings co ON poc.course_offering_id = co.id
            JOIN courses c ON co.course_id = c.id
            LEFT JOIN teachers t ON co.teacher_id = t.id
            LEFT JOIN enrollments e ON po.id = e.package_offering_id AND e.status = 'aceptado'
            GROUP BY p.name, c.name, t.first_name, t.last_name
            HAVING COUNT(DISTINCT e.student_id) > 0
            ORDER BY students_in_package DESC
        """)
        
        for row in package_courses:
            print(f"\n📚 {row['course_name']} (en {row['package_name']})")
            print(f"   Docente: {row['teacher_name']}")
            print(f"   Estudiantes del paquete: {row['students_in_package']}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()
        print("\n🔌 Conexión cerrada")

if __name__ == "__main__":
    asyncio.run(main())
