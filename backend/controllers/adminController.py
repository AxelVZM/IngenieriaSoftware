import asyncpg

async def get_dashboard_data(db: asyncpg.Connection):
    """Get dashboard using the extended view (like Node.js)"""
    dashboard = await db.fetch(
        "SELECT * FROM view_dashboard_admin_extended ORDER BY student_id DESC"
    )
    return [dict(d) for d in dashboard]

async def get_analytics(cycle_id: int, student_id: int, db: asyncpg.Connection):
    """Get analytics summary - matches Node.js logic"""
    sql = "SELECT * FROM analytics_summary WHERE 1=1"
    params = []
    param_index = 1
    
    if cycle_id:
        sql += f" AND cycle_id = ${param_index}"
        params.append(cycle_id)
        param_index += 1
    
    if student_id:
        sql += f" AND student_id = ${param_index}"
        params.append(student_id)
        param_index += 1
    
    sql += " ORDER BY updated_at DESC"
    
    analytics = await db.fetch(sql, *params)
    return [dict(a) for a in analytics]

async def get_notifications(student_id: int, notification_type: str, limit: int, db: asyncpg.Connection):
    """Get notifications - matches Node.js logic"""
    sql = """
        SELECT nl.*, s.first_name, s.last_name, s.dni
        FROM notifications_log nl
        JOIN students s ON nl.student_id = s.id
        WHERE 1=1
    """
    params = []
    param_index = 1
    
    if student_id:
        sql += f" AND nl.student_id = ${param_index}"
        params.append(student_id)
        param_index += 1
    
    if notification_type:
        sql += f" AND nl.type = ${param_index}"
        params.append(notification_type)
        param_index += 1
    
    sql += f" ORDER BY nl.sent_at DESC LIMIT ${param_index}"
    params.append(limit if limit else 50)
    
    notifications = await db.fetch(sql, *params)
    return [dict(n) for n in notifications]

async def get_attendance_absences(cycle_id: int, date_str: str, group_label: str, db: asyncpg.Connection):
    """Get students with absences on specific date, cycle, and group"""
    from datetime import datetime
    
    # Convert string to date
    absence_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    # Query to get students with absences, grouped by student
    students = await db.fetch(
        """SELECT DISTINCT ON (s.id)
               s.id as student_id,
               s.dni,
               s.first_name,
               s.last_name,
               s.phone as student_phone,
               s.parent_name,
               s.parent_phone,
               CASE 
                   WHEN s.parent_phone IS NOT NULL THEN s.parent_phone
                   WHEN s.phone IS NOT NULL THEN s.phone
                   ELSE NULL
               END as phone_to_use,
               CASE 
                   WHEN s.parent_phone IS NOT NULL THEN 'parent'
                   WHEN s.phone IS NOT NULL THEN 'student'
                   ELSE NULL
               END as phone_type,
               array_agg(DISTINCT c.name) as absent_courses,
               COUNT(DISTINCT a.id) as absence_count
           FROM attendance a
           JOIN schedules sch ON a.schedule_id = sch.id
           JOIN course_offerings co ON sch.course_offering_id = co.id
           JOIN courses c ON co.course_id = c.id
           JOIN students s ON a.student_id = s.id
           WHERE a.date = $1
             AND a.status = 'ausente'
             AND co.cycle_id = $2
             AND co.group_label = $3
             AND (s.parent_phone IS NOT NULL OR s.phone IS NOT NULL)
           GROUP BY s.id, s.dni, s.first_name, s.last_name, s.phone, s.parent_name, s.parent_phone
           ORDER BY s.id, s.last_name, s.first_name""",
        absence_date, cycle_id, group_label
    )
    
    return [dict(s) for s in students]

async def send_attendance_notifications(cycle_id: int, date_str: str, group_label: str, db: asyncpg.Connection):
    """Send WhatsApp notifications to parents of students with absences"""
    from datetime import datetime
    from controllers import notificationController
    
    # Get students with absences
    students = await get_attendance_absences(cycle_id, date_str, group_label, db)
    
    success_count = 0
    error_count = 0
    errors = []
    
    for student in students:
        if not student['phone_to_use']:
            error_count += 1
            errors.append(f"{student['dni']} - Sin teléfono")
            continue
        
        # Format courses list
        courses_str = ", ".join(student['absent_courses'])
        
        # Create message
        message = f"Su hijo/a {student['first_name']} {student['last_name']} estuvo ausente el {date_str} en: {courses_str}. Grupo {group_label}"
        
        try:
            # Send WhatsApp message using notificationController
            result = await notificationController.send_whatsapp_message(student['phone_to_use'], message)
            
            if result.get('status') == 'success':
                # Log notification
                await db.execute(
                    """INSERT INTO notifications_log (student_id, parent_phone, type, message, status)
                       VALUES ($1, $2, $3, $4, $5)""",
                    student['student_id'],
                    student['phone_to_use'],
                    'absences_3',
                    message,
                    'sent'
                )
                success_count += 1
            else:
                raise Exception(result.get('message', 'Unknown error'))
                
        except Exception as e:
            error_count += 1
            errors.append(f"{student['dni']} - {str(e)}")
            
            # Log failed notification
            await db.execute(
                """INSERT INTO notifications_log (student_id, parent_phone, type, message, status)
                   VALUES ($1, $2, $3, $4, $5)""",
                student['student_id'],
                student['phone_to_use'],
                'absences_3',
                message,
                'failed'
            )
    
    return {
        "success": success_count,
        "errors": error_count,
        "error_details": errors,
        "total": len(students)
    }

async def get_general_stats(db: asyncpg.Connection):
    stats = {}
    
    # Total students
    result = await db.fetchrow("SELECT COUNT(*) as count FROM students")
    stats['total_students'] = result['count']
    
    # Total teachers
    result = await db.fetchrow("SELECT COUNT(*) as count FROM teachers")
    stats['total_teachers'] = result['count']
    
    # Total courses
    result = await db.fetchrow("SELECT COUNT(*) as count FROM courses")
    stats['total_courses'] = result['count']
    
    # Active enrollments
    result = await db.fetchrow("SELECT COUNT(*) as count FROM enrollments WHERE status = 'aceptado'")
    stats['active_enrollments'] = result['count']
    
    # Pending enrollments
    result = await db.fetchrow("SELECT COUNT(*) as count FROM enrollments WHERE status = 'pendiente'")
    stats['pending_enrollments'] = result['count']
    
    # Total revenue
    result = await db.fetchrow("SELECT COALESCE(SUM(amount), 0) as total FROM installments WHERE status = 'paid'")
    stats['total_revenue'] = float(result['total'])
    
    # Pending payments
    result = await db.fetchrow(
        "SELECT COALESCE(SUM(amount), 0) as total FROM installments WHERE status = 'pending'"
    )
    stats['pending_payments'] = float(result['total'])
    
    return stats
