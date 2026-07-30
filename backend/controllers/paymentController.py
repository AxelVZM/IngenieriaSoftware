import asyncpg
from fastapi import UploadFile
import os
from datetime import datetime, date

async def get_payment_plan(enrollment_id: int, db: asyncpg.Connection):
    plan = await db.fetchrow(
        """SELECT pp.*, e.student_id
           FROM payment_plans pp
           JOIN enrollments e ON pp.enrollment_id = e.id
           WHERE pp.enrollment_id = $1""",
        enrollment_id
    )
    if not plan:
        return None
    return dict(plan)

async def get_installments(payment_plan_id: int, db: asyncpg.Connection):
    installments = await db.fetch(
        """SELECT * FROM installments 
           WHERE payment_plan_id = $1 
           ORDER BY installment_number""",
        payment_plan_id
    )
    return [dict(i) for i in installments]

async def upload_voucher(installment_id: int, file: UploadFile, student_id: int, db: asyncpg.Connection):
    """Upload voucher to Cloudinary"""
    from config.cloudinary import upload_to_cloudinary
    
    # Verify installment exists and permission
    inst = await db.fetchrow(
        """SELECT i.*, pp.enrollment_id, e.student_id 
           FROM installments i 
           JOIN payment_plans pp ON i.payment_plan_id = pp.id 
           JOIN enrollments e ON pp.enrollment_id = e.id 
           WHERE i.id = $1""",
        installment_id
    )
    
    if not inst:
        return {"error": "Installment no encontrado"}
    
    # Read file content
    content = await file.read()
    
    # Generate unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"voucher_{installment_id}_{timestamp}"
    
    # Upload to Cloudinary
    try:
        result = await upload_to_cloudinary(content, filename, folder="Academia-UNI/vouchers")
        voucher_url = result["url"]
    except Exception as e:
        return {"error": f"Error al subir imagen: {str(e)}"}
    
    # Update installment - clear rejection_reason and set status to pending
    await db.execute(
        "UPDATE installments SET voucher_url = $1, status = $2, rejection_reason = NULL WHERE id = $3",
        voucher_url, "pending", installment_id
    )
    
    return {"message": "Voucher subido con éxito", "voucherUrl": voucher_url}

async def approve_installment(installment_id: int, db: asyncpg.Connection):
    """Approve installment - matches Node.js logic exactly"""
    # Mark installment as paid
    await db.execute(
        "UPDATE installments SET status = $1, paid_at = CURRENT_TIMESTAMP WHERE id = $2",
        "paid", installment_id
    )
    
    # Get payment_plan and enrollment
    result = await db.fetchrow(
        """SELECT pp.id as payment_plan_id, pp.enrollment_id 
           FROM payment_plans pp 
           JOIN installments i ON i.payment_plan_id = pp.id 
           WHERE i.id = $1""",
        installment_id
    )
    
    if not result:
        return {"error": "Installment no encontrado"}
    
    payment_plan_id = result['payment_plan_id']
    enrollment_id = result['enrollment_id']
    
    # Check if all installments are paid
    pending = await db.fetchrow(
        "SELECT COUNT(*) as cnt FROM installments WHERE payment_plan_id = $1 AND status != $2",
        payment_plan_id, "paid"
    )
    
    cycle_start_date = None
    cycle_end_date = None
    
    if pending['cnt'] == 0:
        # Accept the main enrollment
        await db.execute(
            "UPDATE enrollments SET status = $1, accepted_at = CURRENT_TIMESTAMP WHERE id = $2",
            "aceptado", enrollment_id
        )
        
        # Get enrollment data for cascade
        enr = await db.fetchrow(
            "SELECT enrollment_type, student_id, course_offering_id, package_offering_id FROM enrollments WHERE id = $1",
            enrollment_id
        )
        
        if enr:
            # Get cycle dates based on enrollment type
            if enr['enrollment_type'] == 'course' and enr['course_offering_id']:
                cy = await db.fetchrow(
                    """SELECT cyc.start_date, cyc.end_date
                       FROM course_offerings co
                       JOIN cycles cyc ON cyc.id = co.cycle_id
                       WHERE co.id = $1""",
                    enr['course_offering_id']
                )
                if cy:
                    cycle_start_date = cy['start_date']
                    cycle_end_date = cy['end_date']
                    
            elif enr['enrollment_type'] == 'package' and enr['package_offering_id']:
                cy = await db.fetchrow(
                    """SELECT cyc.start_date, cyc.end_date
                       FROM package_offerings po
                       JOIN cycles cyc ON cyc.id = po.cycle_id
                       WHERE po.id = $1""",
                    enr['package_offering_id']
                )
                if cy:
                    cycle_start_date = cy['start_date']
                    cycle_end_date = cy['end_date']
                
                # If package, also accept associated course enrollments
                await db.execute(
                    """UPDATE enrollments 
                       SET status = 'aceptado', accepted_at = CURRENT_TIMESTAMP
                       WHERE student_id = $1 AND enrollment_type = 'course' AND package_offering_id = $2""",
                    enr['student_id'], enr['package_offering_id']
                )
    
    # Notify parent (try)
    student = await db.fetchrow(
        """SELECT s.* FROM enrollments e 
           JOIN students s ON e.student_id = s.id 
           WHERE e.id = $1""",
        enrollment_id
    )
    
    if student:
        try:
            from utils.notifications import send_notification_to_parent
            await send_notification_to_parent(
                student['id'],
                student['parent_phone'],
                f"Pago recibido para la matrícula {enrollment_id}",
                "other"
            )
        except Exception as err:
            print(f"Notification error: {err}")
    
    return {
        "message": "Installment aprobado",
        "cycle_start_date": cycle_start_date,
        "cycle_end_date": cycle_end_date
    }

async def get_all_installments(status: str, db: asyncpg.Connection):
    """Get all installments with filters - matches Node.js logic"""
    # Auto-mark overdue installments
    try:
        await db.execute(
            "UPDATE installments SET status = 'overdue' WHERE status = 'pending' AND due_date < CURRENT_DATE"
        )
    except Exception as e:
        print(f"Auto-overdue update failed: {e}")
    
    sql = """SELECT i.*, pp.enrollment_id, e.student_id, s.first_name, s.last_name, s.dni,
                    COALESCE(c.name, p.name) as item_name, e.enrollment_type, e.status AS enrollment_status
             FROM installments i
             JOIN payment_plans pp ON i.payment_plan_id = pp.id
             JOIN enrollments e ON pp.enrollment_id = e.id
             LEFT JOIN students s ON e.student_id = s.id
             LEFT JOIN course_offerings co ON e.course_offering_id = co.id
             LEFT JOIN courses c ON co.course_id = c.id
             LEFT JOIN package_offerings po ON e.package_offering_id = po.id
             LEFT JOIN packages p ON po.package_id = p.id"""
    
    params = []
    if status:
        if status == "rejected":
            sql += " WHERE e.status = 'rechazado'"
        else:
            sql += " WHERE i.status = $1"
            params.append(status)
    
    sql += " ORDER BY i.id DESC"
    
    rows = await db.fetch(sql, *params)
    
    # Derive status_ui (like Node.js)
    mapped = []
    for r in rows:
        row_dict = dict(r)
        row_dict['status_ui'] = 'rejected' if row_dict['enrollment_status'] == 'rechazado' else row_dict['status']
        mapped.append(row_dict)
    
    return mapped

async def reject_installment(installment_id: int, reason: str, db: asyncpg.Connection):
    """Reject installment - matches Node.js logic"""
    result = await db.fetchrow(
        """SELECT i.*, pp.id as payment_plan_id, pp.enrollment_id, i.due_date 
           FROM installments i 
           JOIN payment_plans pp ON i.payment_plan_id = pp.id 
           WHERE i.id = $1""",
        installment_id
    )
    
    if not result:
        return {"error": "Installment no encontrado"}
    
    # Mark installment as overdue if past due date, otherwise pending
    mark = "overdue" if result['due_date'] and result['due_date'] < date.today() else "pending"
    
    await db.execute(
        "UPDATE installments SET status = $1, voucher_url = NULL, rejection_reason = $2 WHERE id = $3",
        mark, reason or None, installment_id
    )
    
    # Mark enrollment as rejected
    await db.execute(
        "UPDATE enrollments SET status = $1 WHERE id = $2",
        "rechazado", result['enrollment_id']
    )
    
    return {"message": "Pago rechazado y matrícula actualizada"}

async def get_pending_payments(db: asyncpg.Connection):
    payments = await db.fetch(
        """SELECT i.*, pp.enrollment_id, e.student_id,
                  s.first_name, s.last_name, s.dni
           FROM installments i
           JOIN payment_plans pp ON i.payment_plan_id = pp.id
           JOIN enrollments e ON pp.enrollment_id = e.id
           JOIN students s ON e.student_id = s.id
           WHERE i.voucher_url IS NOT NULL AND i.status = 'pending'
           ORDER BY i.due_date"""
    )
    return [dict(p) for p in payments]
