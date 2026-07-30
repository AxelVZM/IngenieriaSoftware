"""
Notification routes
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
import asyncpg
from config.database import get_db
from controllers.notificationController import (
    init_whatsapp_session,
    verify_whatsapp_login,
    send_test_message,
    close_whatsapp_session,
    get_rejected_payments,
    get_accepted_payments,
    send_payment_notifications
)

class SendNotificationsRequest(BaseModel):
    type: str  # 'rejected' or 'accepted'
    payments: List[Dict[str, Any]]

router = APIRouter(tags=["notifications"])

@router.post("/notifications/whatsapp/init")
async def init_session():
    """Initialize WhatsApp session and get QR code"""
    return await init_whatsapp_session()

@router.post("/notifications/whatsapp/verify")
async def verify_session():
    """Verify WhatsApp login status"""
    return await verify_whatsapp_login()

@router.post("/notifications/whatsapp/test")
async def test_message(phone: str = "969728039"):
    """Send test message"""
    return await send_test_message(phone)

@router.post("/notifications/whatsapp/close")
async def close_session():
    """Close WhatsApp session"""
    return await close_whatsapp_session()

@router.get("/notifications/payments/rejected")
async def get_rejected(db: asyncpg.Connection = Depends(get_db)):
    """Get list of rejected payments from last 30 days"""
    return await get_rejected_payments(db)

@router.get("/notifications/payments/accepted")
async def get_accepted(db: asyncpg.Connection = Depends(get_db)):
    """Get list of accepted payments from last 7 days"""
    return await get_accepted_payments(db)

@router.post("/notifications/payments/send")
async def send_notifications(request: SendNotificationsRequest):
    """Send WhatsApp notifications for payments"""
    return await send_payment_notifications(request.type, request.payments)
