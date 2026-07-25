from fastapi import APIRouter, Depends, HTTPException, status
from models.enrollment import EnrollmentCreate, EnrollmentStatusUpdate
from middleware.auth import get_current_user, require_role
from config.database import get_db
import asyncpg
import controllers.enrollmentController as enrollmentController

router = APIRouter(prefix="/enrollments", tags=["enrollments"])

@router.get("")
async def get_enrollments(
    student_id: int = None,
    current_user: dict = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db)
):
    # If student, use their ID
    if current_user["role"] == "student":
        student_id = current_user["id"]
    elif current_user["role"] == "admin" and student_id:
        pass
    else:
        raise HTTPException(status_code=400, detail="Falta student_id o no tienes permisos")
    
    return await enrollmentController.get_student_enrollments(student_id, db)

@router.get("/by-offering")
async def get_by_offering(
    type: str,
    id: int,
    status: str = "aceptado",
    db: asyncpg.Connection = Depends(get_db)
):
    if not type or not id:
        raise HTTPException(status_code=400, detail="Faltan parámetros: type e id")
    return await enrollmentController.get_enrollments_by_offering(type, id, status, db)

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_enrollment(
    enrollment: EnrollmentCreate,
    current_user: dict = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db)
):
    student_id = current_user.get("id")
    if not student_id:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    if not enrollment.items or len(enrollment.items) == 0:
        raise HTTPException(status_code=400, detail="No se enviaron items para matricular")
    
    result = await enrollmentController.create_enrollment(student_id, enrollment, db)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.put("/status", dependencies=[Depends(require_role(["admin"]))])
async def update_status(update: EnrollmentStatusUpdate, db: asyncpg.Connection = Depends(get_db)):
    result = await enrollmentController.update_enrollment_status(update, db)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/cancel", dependencies=[Depends(require_role(["student"]))])
async def cancel_enrollment(
    data: dict,
    current_user: dict = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db)
):
    """Cancel own enrollment (student only) - like Node.js"""
    student_id = current_user.get("id")
    if not student_id:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    enrollment_id = data.get("enrollment_id")
    if not enrollment_id:
        raise HTTPException(status_code=400, detail="Falta enrollment_id")
    
    result = await enrollmentController.cancel_enrollment(student_id, enrollment_id, db)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get("/admin", dependencies=[Depends(require_role(["admin"]))])
async def get_admin_enrollments(db: asyncpg.Connection = Depends(get_db)):
    return await enrollmentController.get_admin_enrollments(db)

@router.delete("/{enrollment_id}", dependencies=[Depends(require_role(["admin"]))])
async def delete_enrollment(enrollment_id: int, db: asyncpg.Connection = Depends(get_db)):
    return await enrollmentController.delete_enrollment(enrollment_id, db)
