import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_package_courses():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    try:
        # Check what courses are in "Ciencias Empresariales" package
        package_courses = await conn.fetch("""
            SELECT p.name as package_name, c.name as course_name, 
                   po.id as package_offering_id, co.id as course_offering_id
            FROM packages p
            JOIN package_offerings po ON p.id = po.package_id
            JOIN package_offering_courses poc ON po.id = poc.package_offering_id
            JOIN course_offerings co ON poc.course_offering_id = co.id
            JOIN courses c ON co.course_id = c.id
            WHERE p.name LIKE '%Ciencias Empresariales%'
        """)
        
        print("\n" + "="*80)
        print("COURSES IN 'CIENCIAS EMPRESARIALES' PACKAGE")
        print("="*80)
        
        for row in package_courses:
            print(f"\nPackage: {row['package_name']}")
            print(f"Course: {row['course_name']}")
            print(f"Package Offering ID: {row['package_offering_id']}")
            print(f"Course Offering ID: {row['course_offering_id']}")
            print("-" * 80)
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_package_courses())
