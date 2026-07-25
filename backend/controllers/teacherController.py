import asyncpg
from models.teacher import TeacherCreate, TeacherUpdate, AttendanceCreate

async def get_all_teachers(db: asyncpg.Connection):
    teachers = await db.fetch("SELECT * FROM teachers ORDER BY last_name, first_name")
    # Add 'name' field for frontend compatibility (like Node.js)
    result = []
    for t in teachers:
        teacher_dict = dict(t)
        teacher_dict['name'] = f"{t['first_name']} {t['last_name']}"
        result.append(teacher_dict)
    return result

async def get_teacher_by_id(teacher_id: int, db: asyncpg.Connection):
    teacher = await db.fetchrow("SELECT * FROM teachers WHERE id = $1", teacher_id)
    if not teacher:
        return None
    return dict(teacher)

async def create_teacher(data: TeacherCreate, db: asyncpg.Connection):
    from utils.security import get_password_hash
    
    # Check if DNI already exists
    existing = await db.fetchrow("SELECT id FROM teachers WHERE dni = $1", data.dni)
    if existing:
        return {"error": "Este DNI ya se encuentra registrado"}
    
    # Create user for teacher
    user_result = await db.fetchrow(
        """INSERT INTO users (username, password_hash, role, related_id)
           VALUES ($1, $2, 'teacher', NULL) RETURNING id""",
        data.dni, get_password_hash(data.dni)
    )
    user_id = user_result['id']
    
    # Create teacher
    result = await db.fetchrow(
        """INSERT INTO teachers (first_name, last_name, dni, phone, email, specialization)
           VALUES ($1, $2, $3, $4, $5, $6) RETURNING id""",
        data.first_name, data.last_name, data.dni, data.phone, data.email, data.specialization
    )
    teacher_id = result['id']
    
    # Update user with teacher_id
    await db.execute("UPDATE users SET related_id = $1 WHERE id = $2", teacher_id, user_id)
    
    return {"id": teacher_id, "message": "Docente creado exitosamente"}

async def update_teacher(teacher_id: int, data: TeacherUpdate, db: asyncpg.Connection):
    fields = []
    values = []
    idx = 1
    
    for field, value in data.dict(exclude_unset=True).items():
        fields.append(f"{field} = ${idx}")
        values.append(value)
        idx += 1
    
    if not fields:
        return {"message": "No hay campos para actualizar"}
    
    values.append(teacher_id)
    query = f"UPDATE teachers SET {', '.join(fields)} WHERE id = ${idx}"
    await db.execute(query, *values)
    return {"message": "Docente actualizado correctamente"}

async def delete_teacher(teacher_id: int, db: asyncpg.Connection):
    """Delete teacher - matches Node.js logic"""
    await db.execute("DELETE FROM teachers WHERE id = $1", teacher_id)
    return {"message": "Profesor eliminado correctamente"}

async def reset_teacher_password(teacher_id: int, db: asyncpg.Connection):
    from utils.security import get_password_hash
    
    teacher = await db.fetchrow("SELECT dni FROM teachers WHERE id = $1", teacher_id)
    if not teacher:
        return None
    
    await db.execute(
        "UPDATE users SET password_hash = $1 WHERE username = $2",
        get_password_hash(teacher['dni']), teacher['dni']
    )
    return {"message": "Contraseña reseteada al DNI del docente"}

async def get_teacher_students(teacher_id: int, db: asyncpg.Connection):
    """Get all students enrolled in courses taught by this teacher (direct or via packages)"""
    students = await db.fetch(
        """SELECT DISTINCT s.id, s.dni, s.first_name, s.last_name, s.phone,
                  s.parent_name, s.parent_phone
           FROM students s
           WHERE s.id IN (
               -- Students with direct course enrollment
               SELECT e.student_id
               FROM enrollments e
               JOIN course_offerings co ON e.course_offering_id = co.id
               WHERE co.teacher_id = $1 AND e.status = 'aceptado'
               
               UNION
               
               -- Students with package enrollment
               SELECT e.student_id
               FROM enrollments e
               JOIN package_offering_courses poc ON e.package_offering_id = poc.package_offering_id
               JOIN course_offerings co ON poc.course_offering_id = co.id
               WHERE co.teacher_id = $1 AND e.status = 'aceptado'
           )
           ORDER BY s.last_name, s.first_name""",
        teacher_id
    )
    return [dict(s) for s in students]

async def get_students_by_course_offering(teacher_id: int, course_offering_id: int, db: asyncpg.Connection):
    """Get students enrolled in a specific course offering (direct or via package)"""
    # Verify teacher owns this course offering
    offering = await db.fetchrow(
        "SELECT teacher_id FROM course_offerings WHERE id = $1",
        course_offering_id
    )
    
    if not offering or offering['teacher_id'] != teacher_id:
        return []
    
    students = await db.fetch(
        """SELECT DISTINCT s.id, s.dni, s.first_name, s.last_name, s.phone,
                  s.parent_name, s.parent_phone
           FROM students s
           WHERE s.id IN (
               -- Students with direct course enrollment
               SELECT e.student_id
               FROM enrollments e
               WHERE e.course_offering_id = $1 AND e.status = 'aceptado'
               
               UNION
               
               -- Students with package enrollment
               SELECT e.student_id
               FROM enrollments e
               JOIN package_offering_courses poc ON e.package_offering_id = poc.package_offering_id
               WHERE poc.course_offering_id = $1 AND e.status = 'aceptado'
           )
           ORDER BY s.last_name, s.first_name""",
        course_offering_id
    )
    return [dict(s) for s in students]

async def mark_attendance(teacher_id: int, data: AttendanceCreate, db: asyncpg.Connection):
    """Mark attendance - matches Node.js logic with enrollment check and notifications"""
    from datetime import date, datetime
    
    # Convert string date to date object
    if isinstance(data.date, str):
        attendance_date = datetime.strptime(data.date, '%Y-%m-%d').date()
    else:
        attendance_date = data.date
    
    # Verify teacher owns this schedule
    schedule = await db.fetchrow(
        """SELECT co.teacher_id FROM schedules s
           JOIN course_offerings co ON s.course_offering_id = co.id
           WHERE s.id = $1""",
        data.schedule_id
    )
    
    if not schedule or schedule['teacher_id'] != teacher_id:
        return {"error": "No tienes permiso para marcar asistencia en este curso"}
    
    # Verify student has accepted enrollment (direct or via package)
    # First get the course_offering_id from the schedule
    course_offering = await db.fetchrow(
        """SELECT course_offering_id FROM schedules WHERE id = $1""",
        data.schedule_id
    )
    
    if not course_offering:
        return {"error": "Horario no encontrado"}
    
    enrollment_check = await db.fetchrow(
        """SELECT e.id
           FROM enrollments e
           LEFT JOIN package_offering_courses poc ON e.package_offering_id = poc.package_offering_id
           WHERE (e.course_offering_id = $1 OR poc.course_offering_id = $1)
             AND e.student_id = $2
             AND e.status = 'aceptado'
           LIMIT 1""",
        course_offering['course_offering_id'], data.student_id
    )
    
    if not enrollment_check:
        return {"error": "El estudiante no tiene una matrícula aceptada en este curso"}
    
    # Check if attendance already exists
    existing = await db.fetchrow(
        """SELECT id FROM attendance 
           WHERE student_id = $1 AND schedule_id = $2 AND date = $3""",
        data.student_id, data.schedule_id, attendance_date
    )
    
    if existing:
        await db.execute(
            "UPDATE attendance SET status = $1 WHERE id = $2",
            data.status, existing['id']
        )
    else:
        await db.execute(
            """INSERT INTO attendance (student_id, schedule_id, date, status)
               VALUES ($1, $2, $3, $4)""",
            data.student_id, data.schedule_id, attendance_date, data.status
        )
    
    # If absent, check total absences and notify parent if >= 3 (like Node.js)
    if data.status == "ausente":
        absences = await db.fetchrow(
            """SELECT COUNT(*) as count FROM attendance 
               WHERE student_id = $1 AND status = 'ausente' AND schedule_id = $2""",
            data.student_id, data.schedule_id
        )
        
        if absences and absences['count'] >= 3:
            student = await db.fetchrow(
                "SELECT * FROM students WHERE id = $1",
                data.student_id
            )
            
            if student and student['parent_phone']:
                try:
                    from utils.notifications import send_notification_to_parent
                    await send_notification_to_parent(
                        data.student_id,
                        student['parent_phone'],
                        f"Su hijo/a {student['first_name']} {student['last_name']} ha acumulado {absences['count']} faltas en este horario",
                        "absences_3"
                    )
                except Exception as notif_err:
                    print(f"Error enviando notificación: {notif_err}")
    
    return {"message": "Asistencia marcada correctamente"}

async def get_attendance(teacher_id: int, schedule_id: int, date_str: str, db: asyncpg.Connection):
    """Get attendance records for a schedule and date"""
    from datetime import datetime
    
    # Convert string to date
    attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    # Verify teacher owns this schedule
    schedule = await db.fetchrow(
        """SELECT co.teacher_id FROM schedules s
           JOIN course_offerings co ON s.course_offering_id = co.id
           WHERE s.id = $1""",
        schedule_id
    )
    
    if not schedule or schedule['teacher_id'] != teacher_id:
        return {"error": "No tienes permiso para ver asistencia de este curso"}
    
    # Get attendance records
    records = await db.fetch(
        """SELECT student_id, status
           FROM attendance
           WHERE schedule_id = $1 AND date = $2""",
        schedule_id, attendance_date
    )
    
    return [{"student_id": r['student_id'], "status": r['status']} for r in records]
