from fastapi import APIRouter, Depends, HTTPException, status
from models.teacher import TeacherCreate, TeacherUpdate, AttendanceCreate
from middleware.auth import require_role, get_current_user
from config.database import get_db
import asyncpg
import controllers.teacherController as teacherController

router = APIRouter(prefix="/teachers", tags=["teachers"])

@router.get("", dependencies=[Depends(require_role(["admin"]))])
async def get_teachers(db: asyncpg.Connection = Depends(get_db)):
    return await teacherController.get_all_teachers(db)

@router.get("/{teacher_id}", dependencies=[Depends(require_role(["admin"]))])
async def get_teacher(teacher_id: int, db: asyncpg.Connection = Depends(get_db)):
    teacher = await teacherController.get_teacher_by_id(teacher_id, db)
    if not teacher:
        raise HTTPException(status_code=404, detail="Docente no encontrado")
    return teacher

@router.post("", dependencies=[Depends(require_role(["admin"]))], status_code=status.HTTP_201_CREATED)
async def create_teacher(teacher: TeacherCreate, db: asyncpg.Connection = Depends(get_db)):
    return await teacherController.create_teacher(teacher, db)

@router.put("/{teacher_id}", dependencies=[Depends(require_role(["admin"]))])
async def update_teacher(teacher_id: int, teacher: TeacherUpdate, db: asyncpg.Connection = Depends(get_db)):
    return await teacherController.update_teacher(teacher_id, teacher, db)

@router.delete("/{teacher_id}", dependencies=[Depends(require_role(["admin"]))])
async def delete_teacher(teacher_id: int, db: asyncpg.Connection = Depends(get_db)):
    return await teacherController.delete_teacher(teacher_id, db)

@router.post("/{teacher_id}/reset-password", dependencies=[Depends(require_role(["admin"]))])
async def reset_password(teacher_id: int, db: asyncpg.Connection = Depends(get_db)):
    result = await teacherController.reset_teacher_password(teacher_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="Docente no encontrado")
    return result

@router.get("/{teacher_id}/students", dependencies=[Depends(require_role(["admin", "teacher"]))])
async def get_teacher_students(teacher_id: int, db: asyncpg.Connection = Depends(get_db)):
    return await teacherController.get_teacher_students(teacher_id, db)

@router.get("/{teacher_id}/students/course/{course_offering_id}", dependencies=[Depends(require_role(["teacher"]))])
async def get_students_by_course(teacher_id: int, course_offering_id: int, db: asyncpg.Connection = Depends(get_db)):
    return await teacherController.get_students_by_course_offering(teacher_id, course_offering_id, db)

@router.post("/{teacher_id}/attendance", dependencies=[Depends(require_role(["teacher"]))])
async def mark_attendance(
    teacher_id: int,
    attendance: AttendanceCreate,
    current_user: dict = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db)
):
    result = await teacherController.mark_attendance(teacher_id, attendance, db)
    if result and "error" in result:
        raise HTTPException(status_code=403, detail=result["error"])
    if not result:
        raise HTTPException(status_code=403, detail="No autorizado para este horario")
    return result

@router.get("/{teacher_id}/attendance/{schedule_id}/{date}", dependencies=[Depends(require_role(["teacher"]))])
async def get_attendance(
    teacher_id: int,
    schedule_id: int,
    date: str,
    db: asyncpg.Connection = Depends(get_db)
):
    return await teacherController.get_attendance(teacher_id, schedule_id, date, db)
