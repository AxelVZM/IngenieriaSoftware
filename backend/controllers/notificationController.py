"""
WhatsApp notification controller
"""
import logging
from fastapi import HTTPException
from selenium.common.exceptions import WebDriverException, InvalidSessionIdException
from services.notifications_whatsapp.driver import setup_driver
from services.notifications_whatsapp.session import wait_for_login, verify_login
from services.notifications_whatsapp.sender import send_message

logger = logging.getLogger(__name__)

# Global driver instance
_driver = None


def safe_quit_driver():
    """Safely terminate and reset the global driver instance without raising exceptions"""
    global _driver
    if _driver is not None:
        try:
            _driver.quit()
        except Exception:
            pass
        finally:
            _driver = None


async def init_whatsapp_session():
    """Initialize WhatsApp session and return QR code"""
    global _driver
    
    # Always cleanup existing or dead driver safely first
    safe_quit_driver()
    
    try:
        _driver = setup_driver()
        qr_base64 = wait_for_login(_driver)
        
        if qr_base64 is True:
            return {"status": "already_logged_in", "qr": None}
        
        return {"status": "qr_ready", "qr": qr_base64}
        
    except Exception as e:
        logger.exception("Error initializing WhatsApp session")
        safe_quit_driver()
        raise HTTPException(
            status_code=500,
            detail=f"Error conectando con servicio de WhatsApp (Selenium/Docker): {str(e)}"
        )


async def verify_whatsapp_login():
    """Verify WhatsApp login status"""
    global _driver
    
    if not _driver:
        return {"logged_in": False}
    
    try:
        is_logged = verify_login(_driver)
        return {"logged_in": is_logged}
    except (InvalidSessionIdException, WebDriverException):
        safe_quit_driver()
        return {"logged_in": False}
    except Exception as e:
        safe_quit_driver()
        raise HTTPException(status_code=500, detail=str(e))


async def send_test_message(phone: str):
    """Send test message"""
    global _driver
    
    if not _driver:
        raise HTTPException(
            status_code=400,
            detail="No hay una sesión activa de WhatsApp. Inicia sesión primero."
        )
    
    try:
        result = send_message(_driver, phone, "Mensaje de prueba desde Academia UNI")
        return result
    except (InvalidSessionIdException, WebDriverException) as e:
        safe_quit_driver()
        raise HTTPException(
            status_code=400,
            detail="La sesión de WhatsApp expiró o se cerró. Inicia sesión nuevamente."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def close_whatsapp_session():
    """Close WhatsApp session"""
    safe_quit_driver()
    return {"status": "closed"}


async def send_whatsapp_message(phone: str, message: str):
    """Send WhatsApp message to a phone number"""
    global _driver
    
    if not _driver:
        raise HTTPException(
            status_code=400,
            detail="No hay una sesión activa de WhatsApp. Inicia sesión primero."
        )
    
    try:
        phone = phone.strip()
        if not phone or len(phone) != 9 or not phone.startswith('9'):
            return {
                'status': 'error',
                'message': 'Número de teléfono inválido'
            }
        
        result = send_message(_driver, phone, message)
        return result
        
    except (InvalidSessionIdException, WebDriverException) as e:
        safe_quit_driver()
        return {
            'status': 'error',
            'message': 'La sesión de WhatsApp expiró o se cerró. Vuelva a iniciar sesión.'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }


async def get_rejected_payments(db):
    """Get list of rejected payments from last 30 days"""
    query = """
        SELECT DISTINCT
            s.first_name || ' ' || s.last_name as student_name,
            s.parent_name,
            s.parent_phone,
            i.amount,
            i.rejection_reason,
            COALESCE(c.name, p.name) as course_name,
            i.created_at
        FROM installments i
        JOIN payment_plans pp ON i.payment_plan_id = pp.id
        JOIN enrollments e ON pp.enrollment_id = e.id
        JOIN students s ON e.student_id = s.id
        LEFT JOIN course_offerings co ON e.course_offering_id = co.id
        LEFT JOIN courses c ON co.course_id = c.id
        LEFT JOIN package_offerings po ON e.package_offering_id = po.id
        LEFT JOIN packages p ON po.package_id = p.id
        WHERE i.rejection_reason IS NOT NULL
          AND i.created_at >= NOW() - INTERVAL '30 days'
        ORDER BY i.created_at DESC
    """
    
    results = await db.fetch(query)
    return [dict(row) for row in results]


async def get_accepted_payments(db):
    """Get list of accepted payments from last 7 days"""
    query = """
        SELECT DISTINCT
            s.first_name || ' ' || s.last_name as student_name,
            s.parent_name,
            s.parent_phone,
            i.amount,
            COALESCE(c.name, p.name) as course_name,
            i.paid_at
        FROM installments i
        JOIN payment_plans pp ON i.payment_plan_id = pp.id
        JOIN enrollments e ON pp.enrollment_id = e.id
        JOIN students s ON e.student_id = s.id
        LEFT JOIN course_offerings co ON e.course_offering_id = co.id
        LEFT JOIN courses c ON co.course_id = c.id
        LEFT JOIN package_offerings po ON e.package_offering_id = po.id
        LEFT JOIN packages p ON po.package_id = p.id
        WHERE i.status = 'paid'
          AND e.status = 'aceptado'
          AND i.paid_at >= NOW() - INTERVAL '7 days'
        ORDER BY i.paid_at DESC
    """
    
    results = await db.fetch(query)
    return [dict(row) for row in results]


async def send_payment_notifications(notification_type: str, payments: list):
    """Send WhatsApp notifications for payments"""
    global _driver
    
    if not _driver:
        raise HTTPException(
            status_code=400,
            detail="No hay una sesión activa de WhatsApp. Inicia sesión primero."
        )
    
    results = []
    
    for payment in payments:
        phone = payment.get('parent_phone', '').strip()
        
        # Validate phone number
        if not phone or len(phone) != 9 or not phone.startswith('9'):
            results.append({
                'phone': phone,
                'student': payment.get('student_name', 'Estudiante'),
                'status': 'error',
                'message': 'Número de teléfono inválido (debe tener 9 dígitos y empezar con 9)'
            })
            continue
        
        # Build message based on type
        if notification_type == 'rejected':
            message = f"""🚫 *PAGO RECHAZADO - Academia UNI*

Estimado(a) {payment['parent_name']},

El pago de S/ {payment['amount']:.2f} para el curso *{payment['course_name']}* del estudiante *{payment['student_name']}* ha sido RECHAZADO.

❌ Motivo: {payment.get('rejection_reason', 'No especificado')}

Por favor, suba un nuevo voucher válido desde su panel de estudiante.

Gracias."""
        else:  # accepted
            message = f"""✅ *PAGO APROBADO - Academia UNI*

Estimado(a) {payment['parent_name']},

El pago de S/ {payment['amount']:.2f} para el curso *{payment['course_name']}* del estudiante *{payment['student_name']}* ha sido APROBADO.

✓ Matrícula confirmada
✓ Puede revisar los detalles en el panel de estudiante

¡Gracias por su confianza!"""
        
        try:
            result = send_message(_driver, phone, message)
            results.append({
                'phone': phone,
                'student': payment['student_name'],
                'status': result.get('status', 'error'),
                'message': result.get('message', '')
            })
            
            # Delay between messages to avoid rate limiting
            import time
            time.sleep(2)
            
        except (InvalidSessionIdException, WebDriverException) as e:
            safe_quit_driver()
            results.append({
                'phone': phone,
                'student': payment['student_name'],
                'status': 'error',
                'message': 'La sesión de WhatsApp se cerró o expiró en el navegador.'
            })
            break
        except Exception as e:
            results.append({
                'phone': phone,
                'student': payment['student_name'],
                'status': 'error',
                'message': str(e)
            })
    
    return {
        'total': len(payments),
        'results': results
    }
