from pydantic import BaseModel
from typing import Optional
from datetime import date

class PaymentPlanCreate(BaseModel):
    enrollment_id: int
    total_amount: float
    num_installments: int
    first_due_date: date

class InstallmentUpdate(BaseModel):
    status: str
    paid_amount: Optional[float] = None

class VoucherUpload(BaseModel):
    installment_id: int
