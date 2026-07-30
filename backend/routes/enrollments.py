"""
Rutas del Módulo de Matrículas — versión corregida.

  R-01  /enrollments/by-offering estaba SIN autenticación: cualquiera podía
        obtener nombres, apellidos y DNI de todos los matriculados sin token.
  R-02  GET /enrollments devolvía 400 tanto por falta de parámetro como por
        falta de permisos, mezclando dos causas distintas en un solo código.
  R-03  /enrollments/cancel recibía `data: dict` sin esquema: FastAPI no
        validaba nada ni documentaba el contrato en /docs.
  R-04  El actor del cambio de estado no llegaba al controlador, por lo que
        el historial no podía registrar quién lo hizo.
  R-05  Nuevo endpoint de historial (RNF15).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.enrollment import (
    EnrollmentCreate,
    EnrollmentStatusUpdate,
    EnrollmentCancel,
)
from middleware.auth import get_current_user, require_role
from config.database import get_db
import asyncpg
import controllers.enrollmentController as enrollmentController

router = APIRouter(prefix="/enrollments", tags=["enrollments"])


@router.get("")
async def get_enrollments(
    student_id: int | None = None,
    current_user: dict = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db),
):
    rol = current_user["role"]

    if rol == "student":
        student_id = current_user["id"]          # ignora lo que envíe el cliente
    elif rol == "admin":
        if not student_id:
            # R-02: falta un parámetro -> 400, no 403
            raise HTTPException(
                status_code=400,
                detail="Indica el parámetro student_id para consultar las matrículas "
                       "de un estudiante concreto, o usa /enrollments/admin para verlas todas.",
            )
    else:
        # R-02: no tiene permiso -> 403, no 400
        raise HTTPException(
            status_code=403,
            detail="Tu rol no tiene permiso para consultar matrículas de estudiantes.",
        )

    return await enrollmentController.get_student_enrollments(student_id, db)


@router.get("/by-offering")
async def get_by_offering(
    type: str = Query(..., pattern="^(course|package)$"),
    id: int = Query(..., gt=0),
    status_filter: str = Query("aceptado", alias="status"),
    # R-01: se exige sesión y rol. Este endpoint expone DNI de estudiantes.
    current_user: dict = Depends(require_role(["admin", "teacher"])),
    db: asyncpg.Connection = Depends(get_db),
):
    resultado = await enrollmentController.get_enrollments_by_offering(
        type, id, status_filter, db
    )
    if isinstance(resultado, dict) and "error" in resultado:
        raise HTTPException(status_code=400, detail=resultado["error"])
    return resultado


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_enrollment(
    enrollment: EnrollmentCreate,
    current_user: dict = Depends(require_role(["student"])),
    db: asyncpg.Connection = Depends(get_db),
):
    result = await enrollmentController.create_enrollment(
        current_user["id"], enrollment, db
    )
    if "error" in result:
        raise HTTPException(status_code=409, detail=result["error"])
    return result


@router.put("/status")
async def update_status(
    update: EnrollmentStatusUpdate,
    current_user: dict = Depends(require_role(["admin"])),
    db: asyncpg.Connection = Depends(get_db),
):
    result = await enrollmentController.update_enrollment_status(
        update, db,
        actor_id=current_user["id"],          # R-04
        actor_rol=current_user["role"],
    )
    if "error" in result:
        raise HTTPException(status_code=409, detail=result["error"])
    return result


@router.post("/cancel")
async def cancel_enrollment(
    data: EnrollmentCancel,                    # R-03
    current_user: dict = Depends(require_role(["student"])),
    db: asyncpg.Connection = Depends(get_db),
):
    result = await enrollmentController.cancel_enrollment(
        current_user["id"], data.enrollment_id, db, reason=data.reason
    )
    if "error" in result:
        raise HTTPException(status_code=409, detail=result["error"])
    return result


@router.get("/admin", dependencies=[Depends(require_role(["admin"]))])
async def get_admin_enrollments(db: asyncpg.Connection = Depends(get_db)):
    return await enrollmentController.get_admin_enrollments(db)


@router.get("/{enrollment_id}/history")
async def get_history(
    enrollment_id: int,
    current_user: dict = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db),
):
    """R-05: historial de cambios de estado (RNF15)."""
    enr = await db.fetchrow(
        "SELECT student_id FROM enrollments WHERE id = $1", enrollment_id
    )
    if not enr:
        raise HTTPException(status_code=404, detail="Matrícula no encontrada")

    if current_user["role"] == "student" and enr["student_id"] != current_user["id"]:
        raise HTTPException(
            status_code=403,
            detail="No puedes consultar el historial de una matrícula que no es tuya.",
        )

    return await enrollmentController.obtener_historial(enrollment_id, db)


@router.delete("/{enrollment_id}")
async def delete_enrollment(
    enrollment_id: int,
    current_user: dict = Depends(require_role(["admin"])),
    db: asyncpg.Connection = Depends(get_db),
):
    result = await enrollmentController.delete_enrollment(
        enrollment_id, db, actor_id=current_user["id"]
    )
    if "error" in result:
        codigo = 404 if "no existe" in result["error"] else 409
        raise HTTPException(status_code=codigo, detail=result["error"])
    return result