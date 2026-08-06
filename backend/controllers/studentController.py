import asyncpg
from models.student import StudentCreate, StudentUpdate
from utils.security import get_password_hash  # Fix EST-06: import movido al inicio del archivo

async def get_all_students(db: asyncpg.Connection):
    students = await db.fetch("SELECT * FROM students ORDER BY last_name, first_name")
    return [dict(s) for s in students]

async def get_student_by_id(student_id: int, db: asyncpg.Connection):
    student = await db.fetchrow("SELECT * FROM students WHERE id = $1", student_id)
    if not student:
        return None
    return dict(student)

async def create_student(data: StudentCreate, db: asyncpg.Connection):
    try:
        # Check if DNI already exists
        existing = await db.fetchrow("SELECT id FROM students WHERE dni = $1", data.dni)
        if existing:
            return {"error": "Este DNI ya se encuentra registrado"}

        password_hash = get_password_hash(data.password)
        result = await db.fetchrow(
            """INSERT INTO students (dni, first_name, last_name, phone, parent_name, parent_phone, password_hash)
               VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id""",
            data.dni, data.first_name, data.last_name, data.phone,
            data.parent_name, data.parent_phone, password_hash
        )
        return {"id": result['id'], "message": "Estudiante creado exitosamente"}
    except asyncpg.exceptions.UniqueViolationError:
        return {"error": "Este DNI ya se encuentra registrado"}

async def update_student(student_id: int, data: StudentUpdate, db: asyncpg.Connection):
    fields = []
    values = []
    idx = 1

    for field, value in data.dict(exclude_unset=True).items():
        if field == "password" and value:
            fields.append(f"password_hash = ${idx}")
            values.append(get_password_hash(value))
        else:
            fields.append(f"{field} = ${idx}")
            values.append(value)
        idx += 1

    if not fields:
        return {"message": "No hay campos para actualizar"}

    values.append(student_id)
    query = f"UPDATE students SET {', '.join(fields)} WHERE id = ${idx}"
    await db.execute(query, *values)
    return {"message": "Estudiante actualizado correctamente"}

async def delete_student(student_id: int, db: asyncpg.Connection):
    # Fix BG-U5: valida dependencias antes de borrar.
    enrollments_count = await db.fetchval(
        "SELECT COUNT(*) FROM enrollments WHERE student_id = $1", student_id
    )
    if enrollments_count and enrollments_count > 0:
        return {
            "error": f"No se puede eliminar: el estudiante tiene {enrollments_count} "
                     f"matricula(s) asociada(s). Elimina primero sus matriculas."
        }

    attendance_count = await db.fetchval(
        "SELECT COUNT(*) FROM attendance WHERE student_id = $1", student_id
    )
    if attendance_count and attendance_count > 0:
        return {
            "error": f"No se puede eliminar: el estudiante tiene {attendance_count} "
                     f"registro(s) de asistencia asociado(s)."
        }

    result = await db.execute("DELETE FROM students WHERE id = $1", student_id)
    if result == "DELETE 0":
        return {"error": "Estudiante no encontrado"}

    return {"message": "Estudiante eliminado correctamente"}