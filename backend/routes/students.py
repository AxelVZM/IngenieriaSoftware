from fastapi import APIRouter, Depends, HTTPException, status
from models.student import StudentCreate, StudentUpdate
from middleware.auth import require_role
from config.database import get_db
import asyncpg
import controllers.studentController as studentController

router = APIRouter(prefix="/students", tags=["students"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_student(student: StudentCreate, db: asyncpg.Connection = Depends(get_db)):
    from utils.security import create_access_token
    
    result = await studentController.create_student(student, db)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
        
    token = create_access_token({"id": result['id'], "role": "student"})
    
    return {
        "token": token,
        "user": {
            "id": result['id'],
            "role": "student",
            "first_name": student.first_name,
            "last_name": student.last_name
        }
    }

@router.get("", dependencies=[Depends(require_role(["admin"]))])
async def get_students(db: asyncpg.Connection = Depends(get_db)):
    return await studentController.get_all_students(db)

@router.get("/{student_id}", dependencies=[Depends(require_role(["admin"]))])
async def get_student(student_id: int, db: asyncpg.Connection = Depends(get_db)):
    student = await studentController.get_student_by_id(student_id, db)
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return student

@router.put("/{student_id}", dependencies=[Depends(require_role(["admin"]))])
async def update_student(student_id: int, student: StudentUpdate, db: asyncpg.Connection = Depends(get_db)):
    return await studentController.update_student(student_id, student, db)

@router.delete("/{student_id}", dependencies=[Depends(require_role(["admin"]))])
async def delete_student(student_id: int, db: asyncpg.Connection = Depends(get_db)):
    return await studentController.delete_student(student_id, db)
