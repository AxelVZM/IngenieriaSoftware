"""
Controlador de Pagos — correcciones que afectan al Módulo de Matrículas.

  P-01  IDOR. upload_voucher recibía `student_id` y NUNCA lo comparaba con
        el dueño de la cuota. Cualquier estudiante autenticado podía subir
        un comprobante a la cuota de otro con solo cambiar el installment_id.
  P-02  No se validaba tipo ni tamaño del archivo. El `accept` del input es
        únicamente una sugerencia del navegador: con curl se podía subir
        cualquier binario a Cloudinary.
  P-03  ESTADO INCONSISTENTE PERMANENTE. reject_installment dejaba la
        matrícula en 'rechazado' y la cuota en 'pending'. Cuando el
        estudiante volvía a subir el comprobante, upload_voucher solo tocaba
        `installments`: la matrícula seguía 'rechazado' para siempre, aunque
        el nuevo pago se aprobara. Ahora la resubida devuelve la matrícula a
        'pendiente' y la aprobación puede completar el ciclo.
  P-04  approve_installment ejecutaba el UPDATE antes de comprobar que la
        cuota existiera, y no verificaba si ya estaba pagada (doble clic del
        administrador = doble aprobación).
  P-05  La cascada de aceptación de paquetes estaba duplicada aquí y en
        enrollmentController con lógicas distintas (UPDATE frente a INSERT).
        Ahora ambas rutas invocan enrollmentController.aceptar_matricula.
  P-06  La notificación al apoderado importaba `utils.notifications`, módulo
        que no existe en el proyecto (las notificaciones viven en
        services/notifications_whatsapp). El try/except se tragaba el
        ImportError, de modo que el RF30 nunca llegaba a ejecutarse y nadie
        se enteraba. Ahora se importa el módulo correcto y el fallo se
        registra de forma visible.
  P-07  Ninguna de estas operaciones era transaccional.
"""

import asyncpg
import logging
from fastapi import UploadFile
from datetime import datetime, date

import controllers.enrollmentController as enrollmentController

logger = logging.getLogger(__name__)

TIPOS_IMAGEN_PERMITIDOS = {
    "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp", "application/pdf",
}
TAMANO_MAXIMO_BYTES = 5 * 1024 * 1024  # 5 MB


async def get_payment_plan(enrollment_id: int, db: asyncpg.Connection):
    plan = await db.fetchrow(
        """SELECT pp.*, e.student_id
             FROM payment_plans pp
             JOIN enrollments e ON pp.enrollment_id = e.id
            WHERE pp.enrollment_id = $1""",
        enrollment_id,
    )
    return dict(plan) if plan else None


async def get_installments(payment_plan_id: int, db: asyncpg.Connection):
    filas = await db.fetch(
        """SELECT * FROM installments
            WHERE payment_plan_id = $1
            ORDER BY installment_number""",
        payment_plan_id,
    )
    return [dict(i) for i in filas]


# =====================================================================
# Subida de comprobante
# =====================================================================

async def upload_voucher(installment_id: int, file: UploadFile,
                         student_id: int, db: asyncpg.Connection):
    from config.cloudinary import upload_to_cloudinary

    inst = await db.fetchrow(
        """SELECT i.id, i.status, i.due_date,
                  pp.enrollment_id, e.student_id, e.status AS enrollment_status
             FROM installments i
             JOIN payment_plans pp ON i.payment_plan_id = pp.id
             JOIN enrollments  e  ON pp.enrollment_id = e.id
            WHERE i.id = $1""",
        installment_id,
    )
    if not inst:
        return {"error": "La cuota indicada no existe."}

    # ---- P-01: comprobación de propiedad ----
    if inst["student_id"] != student_id:
        logger.warning(
            "Intento de subida cruzada: estudiante %s sobre la cuota %s (dueño %s)",
            student_id, installment_id, inst["student_id"],
        )
        return {"error": "No puedes subir un comprobante para una cuota que no te pertenece."}

    if inst["status"] == "paid":
        return {"error": "Esta cuota ya figura como pagada. No es necesario subir otro comprobante."}

    if inst["enrollment_status"] == "cancelado":
        return {"error": "Esta matrícula está cancelada; ya no admite pagos."}

    # ---- P-02: validación del archivo ----
    if file.content_type not in TIPOS_IMAGEN_PERMITIDOS:
        return {"error": "Formato no admitido. Sube una imagen JPG, PNG, GIF, WEBP o un PDF."}

    contenido = await file.read()
    if len(contenido) == 0:
        return {"error": "El archivo está vacío. Selecciona un comprobante válido."}
    if len(contenido) > TAMANO_MAXIMO_BYTES:
        return {"error": "El archivo supera los 5 MB. Comprime la imagen e inténtalo de nuevo."}

    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre = f"voucher_{installment_id}_{marca}"

    try:
        resultado = await upload_to_cloudinary(
            contenido, nombre, folder="Academia-UNI/vouchers"
        )
        voucher_url = resultado["url"]
    except Exception as e:
        logger.exception("Fallo al subir el comprobante a Cloudinary")
        return {"error": "No pudimos guardar tu comprobante. Inténtalo de nuevo en unos minutos."}

    # ---- P-03 + P-07: la resubida reactiva la matrícula rechazada ----
    async with db.transaction():
        await db.execute(
            """UPDATE installments
                  SET voucher_url = $1, status = 'pending',
                      rejection_reason = NULL, rejected_at = NULL
                WHERE id = $2""",
            voucher_url, installment_id,
        )

        if inst["enrollment_status"] == "rechazado":
            await db.execute(
                """UPDATE enrollments
                      SET status = 'pendiente', rejected_at = NULL
                    WHERE id = $1""",
                inst["enrollment_id"],
            )
            await enrollmentController.registrar_cambio_estado(
                db, inst["enrollment_id"], "rechazado", "pendiente",
                student_id, "student", "Nuevo comprobante de pago cargado",
            )

    return {"message": "Comprobante subido correctamente", "voucherUrl": voucher_url}


# =====================================================================
# Aprobación
# =====================================================================

async def approve_installment(installment_id: int, db: asyncpg.Connection,
                              actor_id: int = None, actor_rol: str = None):
    # ---- P-04: comprobar ANTES de escribir ----
    fila = await db.fetchrow(
        """SELECT i.id, i.status, i.voucher_url,
                  pp.id AS payment_plan_id, pp.enrollment_id
             FROM installments i
             JOIN payment_plans pp ON i.payment_plan_id = pp.id
            WHERE i.id = $1""",
        installment_id,
    )
    if not fila:
        return {"error": "La cuota indicada no existe."}
    if fila["status"] == "paid":
        return {"error": "Esta cuota ya fue aprobada anteriormente."}
    if not fila["voucher_url"]:
        return {"error": "No se puede aprobar una cuota sin comprobante de pago cargado."}

    enrollment_id = fila["enrollment_id"]
    inicio_ciclo = fin_ciclo = None

    async with db.transaction():
        await db.execute(
            """UPDATE installments
                  SET status = 'paid', paid_at = CURRENT_TIMESTAMP,
                      rejection_reason = NULL
                WHERE id = $1""",
            installment_id,
        )

        pendientes = await db.fetchval(
            "SELECT COUNT(*) FROM installments WHERE payment_plan_id = $1 AND status <> 'paid'",
            fila["payment_plan_id"],
        )

        if pendientes == 0:
            # ---- P-05: un único punto de aceptación ----
            resultado = await enrollmentController.aceptar_matricula(
                db, enrollment_id, actor_id, actor_rol
            )
            if "error" in resultado:
                return resultado

            ciclo = await db.fetchrow(
                """SELECT cyc.start_date, cyc.end_date
                     FROM enrollments e
                     LEFT JOIN course_offerings  co  ON e.course_offering_id = co.id
                     LEFT JOIN package_offerings po  ON e.package_offering_id = po.id
                     LEFT JOIN cycles            cyc ON cyc.id = COALESCE(co.cycle_id, po.cycle_id)
                    WHERE e.id = $1""",
                enrollment_id,
            )
            if ciclo:
                inicio_ciclo, fin_ciclo = ciclo["start_date"], ciclo["end_date"]

    # ---- P-06: notificación fuera de la transacción, con módulo correcto ----
    await _notificar_apoderado(
        enrollment_id, db,
        f"Se ha aprobado el pago de la matrícula #{enrollment_id}.",
    )

    return {
        "message": "Cuota aprobada correctamente",
        "cycle_start_date": inicio_ciclo,
        "cycle_end_date": fin_ciclo,
        "enrollment_aceptada": pendientes == 0,
    }


# =====================================================================
# Rechazo
# =====================================================================

async def reject_installment(installment_id: int, reason: str, db: asyncpg.Connection,
                             actor_id: int = None, actor_rol: str = None):
    if not reason or not reason.strip():
        return {"error": "Debes indicar el motivo del rechazo para que el estudiante pueda corregirlo."}

    fila = await db.fetchrow(
        """SELECT i.id, i.status, i.due_date,
                  pp.enrollment_id, e.status AS enrollment_status
             FROM installments i
             JOIN payment_plans pp ON i.payment_plan_id = pp.id
             JOIN enrollments  e  ON pp.enrollment_id = e.id
            WHERE i.id = $1""",
        installment_id,
    )
    if not fila:
        return {"error": "La cuota indicada no existe."}
    if fila["status"] == "paid":
        return {"error": "Esta cuota ya fue aprobada; no puede rechazarse."}

    marca = "overdue" if fila["due_date"] and fila["due_date"] < date.today() else "pending"

    async with db.transaction():
        await db.execute(
            """UPDATE installments
                  SET status = $1, voucher_url = NULL,
                      rejection_reason = $2, rejected_at = CURRENT_TIMESTAMP
                WHERE id = $3""",
            marca, reason.strip(), installment_id,
        )
        await db.execute(
            "UPDATE enrollments SET status = 'rechazado', rejected_at = CURRENT_TIMESTAMP WHERE id = $1",
            fila["enrollment_id"],
        )
        await enrollmentController.registrar_cambio_estado(
            db, fila["enrollment_id"], fila["enrollment_status"], "rechazado",
            actor_id, actor_rol, reason.strip(),
        )

    await _notificar_apoderado(
        fila["enrollment_id"], db,
        f"El comprobante de la matrícula #{fila['enrollment_id']} fue rechazado. Motivo: {reason.strip()}",
    )

    return {"message": "Pago rechazado. El estudiante puede subir un nuevo comprobante."}


# =====================================================================
# Consultas
# =====================================================================

async def get_all_installments(status: str, db: asyncpg.Connection):
    try:
        await db.execute(
            "UPDATE installments SET status = 'overdue' "
            "WHERE status = 'pending' AND due_date < CURRENT_DATE"
        )
    except Exception:
        logger.exception("No se pudo marcar cuotas vencidas")

    sql = """SELECT i.*, pp.enrollment_id, e.student_id,
                    s.first_name, s.last_name, s.dni,
                    COALESCE(c.name, p.name) AS item_name,
                    e.enrollment_type, e.status AS enrollment_status
               FROM installments i
               JOIN payment_plans pp ON i.payment_plan_id = pp.id
               JOIN enrollments  e  ON pp.enrollment_id = e.id
               LEFT JOIN students          s  ON e.student_id = s.id
               LEFT JOIN course_offerings  co ON e.course_offering_id = co.id
               LEFT JOIN courses           c  ON co.course_id = c.id
               LEFT JOIN package_offerings po ON e.package_offering_id = po.id
               LEFT JOIN packages          p  ON po.package_id = p.id"""

    params = []
    if status:
        if status == "rejected":
            sql += " WHERE e.status = 'rechazado'"
        else:
            sql += " WHERE i.status = $1"
            params.append(status)

    sql += " ORDER BY i.id DESC"
    filas = await db.fetch(sql, *params)

    salida = []
    for f in filas:
        d = dict(f)
        d["status_ui"] = "rejected" if d["enrollment_status"] == "rechazado" else d["status"]
        salida.append(d)
    return salida


async def get_pending_payments(db: asyncpg.Connection):
    filas = await db.fetch(
        """SELECT i.*, pp.enrollment_id, e.student_id,
                  s.first_name, s.last_name, s.dni
             FROM installments i
             JOIN payment_plans pp ON i.payment_plan_id = pp.id
             JOIN enrollments  e  ON pp.enrollment_id = e.id
             JOIN students     s  ON e.student_id = s.id
            WHERE i.voucher_url IS NOT NULL AND i.status = 'pending'
            ORDER BY i.due_date"""
    )
    return [dict(p) for p in filas]


# =====================================================================
# Notificación (P-06)
# =====================================================================

async def _notificar_apoderado(enrollment_id: int, db: asyncpg.Connection, mensaje: str):
    estudiante = await db.fetchrow(
        """SELECT s.id, s.parent_phone
             FROM enrollments e
             JOIN students s ON e.student_id = s.id
            WHERE e.id = $1""",
        enrollment_id,
    )
    if not estudiante or not estudiante["parent_phone"]:
        logger.info("Matrícula %s sin teléfono de apoderado: no se notifica", enrollment_id)
        return

    try:
        # Módulo correcto: services/notifications_whatsapp/sender.py
        from services.notifications_whatsapp.sender import send_message
        await send_message(estudiante["parent_phone"], mensaje)
    except ImportError:
        logger.error(
            "RF30 no operativo: no se encontró services.notifications_whatsapp.sender. "
            "La notificación de la matrícula %s no se envió.", enrollment_id,
        )
    except Exception:
        logger.exception("Fallo al notificar por WhatsApp la matrícula %s", enrollment_id)