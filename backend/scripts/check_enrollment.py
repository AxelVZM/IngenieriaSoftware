import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_enrollment():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    try:
        # Check enrollment for DNI 87878787
        enrollments = await conn.fetch("""
            SELECT e.id, e.student_id, s.dni, s.first_name, s.last_name, 
                   e.status, e.enrollment_type,
                   COALESCE(c.name, p.name) as enrolled_in
            FROM enrollments e
            JOIN students s ON s.id = e.student_id
            LEFT JOIN course_offerings co ON e.course_offering_id = co.id
            LEFT JOIN courses c ON co.course_id = c.id
            LEFT JOIN package_offerings po ON e.package_offering_id = po.id
            LEFT JOIN packages p ON po.package_id = p.id
            WHERE s.dni = '87878787'
        """)
        
        print("\n" + "="*80)
        print("ENROLLMENT STATUS FOR DNI: 87878787")
        print("="*80)
        
        if not enrollments:
            print("No enrollments found")
        else:
            for e in enrollments:
                print(f"\nEnrollment ID: {e['id']}")
                print(f"Student: {e['first_name']} {e['last_name']}")
                print(f"Type: {e['enrollment_type']}")
                print(f"Status: {e['status']}")
                print(f"Enrolled in: {e['enrolled_in']}")
                print("-" * 80)
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_enrollment())
