import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def cleanup_duplicate_enrollments():
    """
    Remove duplicate enrollments keeping:
    1. 'aceptado' status over others
    2. Most recent enrollment if same status
    """
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    try:
        # Find duplicates for course enrollments
        course_duplicates = await conn.fetch("""
            SELECT student_id, course_offering_id, 
                   array_agg(id ORDER BY 
                       CASE status 
                           WHEN 'aceptado' THEN 1 
                           WHEN 'pendiente' THEN 2 
                           WHEN 'rechazado' THEN 3 
                           WHEN 'cancelado' THEN 4 
                       END,
                       registered_at DESC
                   ) as enrollment_ids
            FROM enrollments
            WHERE course_offering_id IS NOT NULL
            GROUP BY student_id, course_offering_id
            HAVING COUNT(*) > 1
        """)
        
        # Find duplicates for package enrollments
        package_duplicates = await conn.fetch("""
            SELECT student_id, package_offering_id,
                   array_agg(id ORDER BY 
                       CASE status 
                           WHEN 'aceptado' THEN 1 
                           WHEN 'pendiente' THEN 2 
                           WHEN 'rechazado' THEN 3 
                           WHEN 'cancelado' THEN 4 
                       END,
                       registered_at DESC
                   ) as enrollment_ids
            FROM enrollments
            WHERE package_offering_id IS NOT NULL
            GROUP BY student_id, package_offering_id
            HAVING COUNT(*) > 1
        """)
        
        total_deleted = 0
        
        print("\n" + "="*80)
        print("CLEANING DUPLICATE ENROLLMENTS")
        print("="*80)
        
        # Process course duplicates
        for dup in course_duplicates:
            ids_to_delete = dup['enrollment_ids'][1:]  # Keep first (best), delete rest
            print(f"\nStudent {dup['student_id']}, Course Offering {dup['course_offering_id']}")
            print(f"  Keeping enrollment ID: {dup['enrollment_ids'][0]}")
            print(f"  Deleting IDs: {ids_to_delete}")
            
            deleted = await conn.execute(
                "DELETE FROM enrollments WHERE id = ANY($1)",
                ids_to_delete
            )
            total_deleted += len(ids_to_delete)
        
        # Process package duplicates
        for dup in package_duplicates:
            ids_to_delete = dup['enrollment_ids'][1:]  # Keep first (best), delete rest
            print(f"\nStudent {dup['student_id']}, Package Offering {dup['package_offering_id']}")
            print(f"  Keeping enrollment ID: {dup['enrollment_ids'][0]}")
            print(f"  Deleting IDs: {ids_to_delete}")
            
            deleted = await conn.execute(
                "DELETE FROM enrollments WHERE id = ANY($1)",
                ids_to_delete
            )
            total_deleted += len(ids_to_delete)
        
        print("\n" + "="*80)
        print(f"CLEANUP COMPLETE: Deleted {total_deleted} duplicate enrollments")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"ERROR: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    print("\n⚠️  WARNING: This will DELETE duplicate enrollments from the database!")
    print("Press Ctrl+C to cancel, or Enter to continue...")
    input()
    asyncio.run(cleanup_duplicate_enrollments())
