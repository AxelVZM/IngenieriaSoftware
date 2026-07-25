from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from middleware.auth import require_role, get_current_user
from config.database import get_db
import asyncpg
import controllers.paymentController as paymentController

router = APIRouter(prefix="/payments", tags=["payments"])

# Get all installments with optional status filter (like Node.js)
@router.get("", dependencies=[Depends(require_role(["admin"]))])
async def get_payments(status: str = None, db: asyncpg.Connection = Depends(get_db)):
    return await paymentController.get_all_installments(status, db)

@router.get("/pending", dependencies=[Depends(require_role(["admin"]))])
async def get_pending(db: asyncpg.Connection = Depends(get_db)):
    return await paymentController.get_pending_payments(db)

@router.get("/plan/{enrollment_id}")
async def get_plan(enrollment_id: int, db: asyncpg.Connection = Depends(get_db)):
    plan = await paymentController.get_payment_plan(enrollment_id, db)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan de pago no encontrado")
    return plan

@router.get("/installments/{payment_plan_id}")
async def get_installments(payment_plan_id: int, db: asyncpg.Connection = Depends(get_db)):
    return await paymentController.get_installments(payment_plan_id, db)

@router.post("/upload-voucher/{installment_id}")
async def upload_voucher(
    installment_id: int,
    file: UploadFile = File(..., alias="voucher"),
    current_user: dict = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db)
):
    student_id = current_user.get("id")
    result = await paymentController.upload_voucher(installment_id, file, student_id, db)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@router.post("/upload")
async def upload_voucher_alt(
    file: UploadFile = File(..., alias="voucher"),
    installment_id: int = Form(None),
    current_user: dict = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db)
):
    """Alternative upload endpoint for compatibility (like Node.js) - accepts Form data"""
    if not installment_id:
        raise HTTPException(status_code=400, detail="installment_id es requerido")
    student_id = current_user.get("id")
    result = await paymentController.upload_voucher(installment_id, file, student_id, db)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

# Approve installment (like Node.js)
@router.post("/approve", dependencies=[Depends(require_role(["admin"]))])
async def approve_post(data: dict, db: asyncpg.Connection = Depends(get_db)):
    installment_id = data.get("installment_id")
    if not installment_id:
        raise HTTPException(status_code=400, detail="installment_id es requerido")
    result = await paymentController.approve_installment(installment_id, db)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

# Reject installment (like Node.js)
@router.post("/reject", dependencies=[Depends(require_role(["admin"]))])
async def reject_post(data: dict, db: asyncpg.Connection = Depends(get_db)):
    print(f"DEBUG reject_post received data: {data}")  # Debug log
    installment_id = data.get("installment_id")
    reason = data.get("reason")
    print(f"DEBUG installment_id: {installment_id}, reason: {reason}")  # Debug log
    if not installment_id:
        raise HTTPException(status_code=400, detail=f"installment_id es requerido. Received: {data}")
    result = await paymentController.reject_installment(installment_id, reason, db)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
