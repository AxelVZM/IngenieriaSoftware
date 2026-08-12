"""
Controlador del Módulo de Matrículas — versión corregida.

Correcciones aplicadas respecto a la versión revisada:
  C-01  create_enrollment ahora es transaccional (todo o nada).
  C-02  Se valida que la oferta exista y tenga precio > 0 antes de matricular.
  C-03  cancel_enrollment ya NO borra la fila: cambia el estado a 'cancelado'.
  C-04  update_enrollment_status valida la transición contra una máquina de
        estados explícita, en lugar de aceptar cualquier cadena.
  C-05  Todo cambio de estado queda registrado en enrollment_status_history.
  C-06  Se incorpora el estado 'finalizado' al flujo.
  C-07  Al rechazar/cancelar una matrícula de paquete, se propaga el estado
        a las matrículas de curso hijas (antes quedaban en 'aceptado').
  C-08  La cascada de aceptación de paquete vive en UNA sola función,
        reutilizada por el controlador de pagos.
  C-09  get_enrollments_by_offering valida el parámetro `type` en lugar de
        convertir en silencio cualquier valor a 'package'.
  C-10  delete_enrollment verifica existencia y bloquea el borrado de
        matrículas con pagos aprobados.
  C-11  Se respeta la capacidad (capacity) de la oferta si está definida.
  C-12  INT-07/FUN-02: la validación de duplicados (PASO 1) no cierra la
        condición de carrera entre dos peticiones simultáneas — ambas pueden
        pasar el SELECT antes de que cualquiera inserte. La BD tiene ahora
        índices únicos parciales (ux_enrollments_course_active /
        ux_enrollments_package_active) que garantizan RF13 al nivel de
        motor; create_enrollment traduce esa violación en un error legible.
  C-13  Los `return {"error": ...}` dentro de la transacción NO revertían
        los ítems ya insertados en el mismo lote: `async with db.transaction()`
        solo hace rollback si se propaga una excepción, no ante un `return`
        normal. Un carrito de 2 ítems donde el segundo fallaba en el PASO 2
        (precio inválido) dejaba el primero matriculado pese al mensaje de
        error. Ahora los errores se señalizan con una excepción interna para
        que la transacción SIEMPRE haga rollback si no se completa el lote.
"""

import asyncpg
from datetime import date, timedelta
from typing import Optional

from models.enrollment import (
    EnrollmentCreate,
    EnrollmentStatusUpdate,
    EnrollmentStatus,
    TRANSICIONES_VALIDAS,
    ETIQUETAS_ESTADO,
)

ESTADOS_ACTIVOS = ("pendiente", "aceptado", "finalizado")


class _RegistroInvalido(Exception):
    """C-13: error de validación de negocio dentro de create_enrollment.

    Se usa en vez de `return` para que la transacción haga rollback de
    cualquier ítem ya insertado en el mismo lote antes de reportar el error.
    """


# =====================================================================
# Utilidades internas
# =====================================================================

async def registrar_cambio_estado(
    db: asyncpg.Connection,
    enrollment_id: int,
    estado_anterior: Optional[str],
    estado_nuevo: str,
    actor_id: Optional[int] = None,
    actor_rol: Optional[str] = None,
    motivo: Optional[str] = None,
):
    """C-05: deja rastro de cada transición (RNF15 — trazabilidad)."""
    await db.execute(
        """INSERT INTO enrollment_status_history
             (enrollment_id, previous_status, new_status,
              changed_by_id, changed_by_role, reason)
           VALUES ($1, $2, $3, $4, $5, $6)""",
        enrollment_id, estado_anterior, estado_nuevo,
        actor_id, actor_rol, motivo,
    )


async def obtener_historial(enrollment_id: int, db: asyncpg.Connection):
    filas = await db.fetch(
        """SELECT previous_status, new_status, changed_by_role,
                  reason, changed_at
             FROM enrollment_status_history
            WHERE enrollment_id = $1
            ORDER BY changed_at DESC""",
        enrollment_id,
    )
    return [dict(f) for f in filas]


async def _plazas_disponibles(db: asyncpg.Connection, tipo: str, offering_id: int) -> Optional[int]:
    """C-11: devuelve plazas libres, o None si la oferta no declara capacidad."""
    tabla = "course_offerings" if tipo == "course" else "package_offerings"
    columna = "course_offering_id" if tipo == "course" else "package_offering_id"

    fila = await db.fetchrow(f"SELECT capacity FROM {tabla} WHERE id = $1", offering_id)
    if not fila or fila["capacity"] is None:
        return None

    ocupadas = await db.fetchval(
        f"""SELECT COUNT(*) FROM enrollments
             WHERE {columna} = $1
               AND enrollment_type = $2
               AND status = ANY($3::text[])""",
        offering_id, tipo, list(ESTADOS_ACTIVOS),
    )
    return int(fila["capacity"]) - int(ocupadas)


async def aceptar_matricula(
    db: asyncpg.Connection,
    enrollment_id: int,
    actor_id: Optional[int] = None,
    actor_rol: Optional[str] = None,
) -> dict:
    """
    C-08: ÚNICO punto de aceptación de una matrícula.

    Antes existían dos implementaciones divergentes de la misma regla:
    paymentController.approve_installment hacía UPDATE sobre matrículas de
    curso ya existentes, mientras que update_enrollment_status hacía INSERT
    de matrículas nuevas. El resultado dependía de por dónde entrara el
    flujo. Ahora ambas rutas llaman aquí.
    """
    enr = await db.fetchrow(
        """SELECT id, student_id, status, enrollment_type, package_offering_id
             FROM enrollments WHERE id = $1""",
        enrollment_id,
    )
    if not enr:
        return {"error": "Matrícula no encontrada"}

    estado_anterior = enr["status"]

    await db.execute(
        """UPDATE enrollments
              SET status = 'aceptado', accepted_at = CURRENT_TIMESTAMP
            WHERE id = $1""",
        enrollment_id,
    )
    await registrar_cambio_estado(
        db, enrollment_id, estado_anterior, "aceptado",
        actor_id, actor_rol, "Pago aprobado",
    )

    cursos_afectados = 0
    if enr["enrollment_type"] == "package" and enr["package_offering_id"]:
        ofertas = await db.fetch(
            """SELECT course_offering_id FROM package_offering_courses
                WHERE package_offering_id = $1""",
            enr["package_offering_id"],
        )
        for oferta in ofertas:
            hija = await db.fetchrow(
                """SELECT id, status FROM enrollments
                    WHERE student_id = $1
                      AND course_offering_id = $2
                      AND package_offering_id = $3""",
                enr["student_id"], oferta["course_offering_id"],
                enr["package_offering_id"],
            )
            if hija is None:
                nueva = await db.fetchrow(
                    """INSERT INTO enrollments
                         (student_id, course_offering_id, package_offering_id,
                          enrollment_type, status, registered_at, accepted_at)
                       VALUES ($1, $2, $3, 'course', 'aceptado',
                               CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                       RETURNING id""",
                    enr["student_id"], oferta["course_offering_id"],
                    enr["package_offering_id"],
                )
                await registrar_cambio_estado(
                    db, nueva["id"], None, "aceptado", actor_id, actor_rol,
                    f"Alta automática por aceptación del paquete #{enrollment_id}",
                )
                cursos_afectados += 1
            elif hija["status"] != "aceptado":
                await db.execute(
                    """UPDATE enrollments
                          SET status = 'aceptado', accepted_at = CURRENT_TIMESTAMP
                        WHERE id = $1""",
                    hija["id"],
                )
                await registrar_cambio_estado(
                    db, hija["id"], hija["status"], "aceptado", actor_id, actor_rol,
                    f"Sincronización con el paquete #{enrollment_id}",
                )
                cursos_afectados += 1

    return {"ok": True, "cursos_afectados": cursos_afectados}


async def _propagar_a_cursos_del_paquete(
    db: asyncpg.Connection,
    enr: asyncpg.Record,
    estado_nuevo: str,
    actor_id: Optional[int],
    actor_rol: Optional[str],
    motivo: Optional[str],
) -> int:
    """
    C-07: si se rechaza o cancela un paquete, sus cursos hijos no pueden
    seguir en 'aceptado'. Este era el origen de los "estados inconsistentes".
    """
    if enr["enrollment_type"] != "package" or not enr["package_offering_id"]:
        return 0

    hijas = await db.fetch(
        """SELECT id, status FROM enrollments
            WHERE student_id = $1
              AND enrollment_type = 'course'
              AND package_offering_id = $2
              AND status = ANY($3::text[])""",
        enr["student_id"], enr["package_offering_id"], list(ESTADOS_ACTIVOS),
    )
    for hija in hijas:
        await db.execute(
            "UPDATE enrollments SET status = $1 WHERE id = $2",
            estado_nuevo, hija["id"],
        )
        await registrar_cambio_estado(
            db, hija["id"], hija["status"], estado_nuevo, actor_id, actor_rol,
            motivo or f"Propagado desde el paquete #{enr['id']}",
        )
    return len(hijas)


# =====================================================================
# Consultas
# =====================================================================

async def get_student_enrollments(student_id: int, db: asyncpg.Connection):
    """
    Matrículas de un estudiante con sus cuotas.
    C-05b: se añade `status_label` para que la interfaz no tenga que
    traducir estados por su cuenta en tres componentes distintos.
    """
    enrollments = await db.fetch(
        """SELECT e.*,
                  COALESCE(c.name, p.name) AS item_name,
                  COALESCE(COALESCE(co.price_override, c.base_price),
                           COALESCE(po.price_override, p.base_price)) AS item_price,
                  COALESCE(co.group_label, po.group_label) AS group_label,
                  cyc.name       AS cycle_name,
                  cyc.start_date AS cycle_start_date,
                  cyc.end_date   AS cycle_end_date,
                  pp.id           AS payment_plan_id,
                  pp.total_amount,
                  pp.installments AS total_installments,
                  (
                    SELECT STRING_AGG(
                             c2.name ||
                             CASE WHEN co2.group_label IS NOT NULL
                                       AND co2.group_label <> ''
                                  THEN ' (Grupo ' || co2.group_label || ')'
                                  ELSE '' END,
                             ', ')
                      FROM enrollments e2
                      JOIN course_offerings co2 ON e2.course_offering_id = co2.id
                      JOIN courses c2 ON co2.course_id = c2.id
                     WHERE e2.student_id = e.student_id
                       AND e2.enrollment_type = 'course'
                       AND e2.status <> 'cancelado'
                       AND e2.package_offering_id = e.package_offering_id
                  ) AS package_courses_summary
             FROM enrollments e
             LEFT JOIN course_offerings  co  ON e.course_offering_id = co.id
             LEFT JOIN courses           c   ON co.course_id = c.id
             LEFT JOIN package_offerings po  ON e.package_offering_id = po.id
             LEFT JOIN packages          p   ON po.package_id = p.id
             LEFT JOIN cycles            cyc ON cyc.id = COALESCE(co.cycle_id, po.cycle_id)
             LEFT JOIN payment_plans     pp  ON pp.enrollment_id = e.id
            WHERE e.student_id = $1
            ORDER BY e.registered_at DESC""",
        student_id,
    )

    resultado = []
    for fila in enrollments:
        d = dict(fila)
        try:
            d["status_label"] = ETIQUETAS_ESTADO[EnrollmentStatus(d["status"])]
        except ValueError:
            d["status_label"] = d["status"]

        if d.get("payment_plan_id"):
            cuotas = await db.fetch(
                """SELECT * FROM installments
                    WHERE payment_plan_id = $1
                    ORDER BY installment_number""",
                d["payment_plan_id"],
            )
            d["installments"] = [dict(i) for i in cuotas]
        else:
            d["installments"] = []
        resultado.append(d)

    return resultado


async def get_enrollments_by_offering(type: str, id: int, status: str, db: asyncpg.Connection):
    """
    C-09: antes, `params = [type if type == "course" else "package", ...]`
    convertía cualquier valor desconocido en 'package' sin avisar, de modo
    que `?type=basura` devolvía silenciosamente la lista de paquetes.
    """
    if type not in ("course", "package"):
        return {"error": "El parámetro 'type' debe ser 'course' o 'package'"}

    estados_validos = {e.value for e in EnrollmentStatus}
    if status not in estados_validos:
        return {"error": f"Estado no válido. Valores admitidos: {', '.join(sorted(estados_validos))}"}

    columna = "e.course_offering_id" if type == "course" else "e.package_offering_id"

    filas = await db.fetch(
        f"""SELECT e.id AS enrollment_id,
                   e.enrollment_type,
                   e.status,
                   s.id AS student_id, s.first_name, s.last_name, s.dni,
                   COALESCE(c.name, p.name) AS item_name
              FROM enrollments e
              JOIN students s ON s.id = e.student_id
              LEFT JOIN course_offerings  co ON e.course_offering_id = co.id
              LEFT JOIN courses           c  ON co.course_id = c.id
              LEFT JOIN package_offerings po ON e.package_offering_id = po.id
              LEFT JOIN packages          p  ON po.package_id = p.id
             WHERE e.enrollment_type = $1
               AND e.status = $2
               AND {columna} = $3
             ORDER BY s.last_name, s.first_name""",
        type, status, id,
    )
    return [dict(f) for f in filas]


async def get_admin_enrollments(db: asyncpg.Connection):
    """
    C-12: la consulta original no devolvía `payment_status` ni `voucher_url`,
    pero AdminEnrollments.jsx los leía. El resultado era una columna "Pago"
    permanentemente en "sin pago" y un botón Aprobar que nunca se mostraba.
    """
    filas = await db.fetch(
        """SELECT e.*, s.first_name, s.last_name, s.dni,
                  COALESCE(c.name, p.name) AS item_name,
                  COALESCE(co.group_label, po.group_label) AS group_label,
                  cyc.name AS cycle_name,
                  pp.id AS payment_plan_id,
                  pp.total_amount,
                  i.id           AS installment_id,
                  i.status       AS payment_status,
                  i.voucher_url,
                  i.rejection_reason,
                  i.due_date
             FROM enrollments e
             JOIN students s ON e.student_id = s.id
             LEFT JOIN course_offerings  co  ON e.course_offering_id = co.id
             LEFT JOIN courses           c   ON co.course_id = c.id
             LEFT JOIN package_offerings po  ON e.package_offering_id = po.id
             LEFT JOIN packages          p   ON po.package_id = p.id
             LEFT JOIN cycles            cyc ON cyc.id = COALESCE(co.cycle_id, po.cycle_id)
             LEFT JOIN payment_plans     pp  ON pp.enrollment_id = e.id
             LEFT JOIN LATERAL (
                   SELECT * FROM installments ii
                    WHERE ii.payment_plan_id = pp.id
                    ORDER BY ii.installment_number
                    LIMIT 1
             ) i ON TRUE
            ORDER BY e.registered_at DESC"""
    )

    salida = []
    for fila in filas:
        d = dict(fila)
        try:
            d["status_label"] = ETIQUETAS_ESTADO[EnrollmentStatus(d["status"])]
        except ValueError:
            d["status_label"] = d["status"]
        salida.append(d)
    return salida


# =====================================================================
# Alta de matrículas
# =====================================================================

async def create_enrollment(student_id: int, data: EnrollmentCreate, db: asyncpg.Connection):
    try:
        async with db.transaction():

            # ---------- PASO 1: validación previa de todos los ítems ----------
            for item in data.items:
                tipo = item.type.value

                if tipo == "course":
                    existente = await db.fetchrow(
                        """SELECT c.name AS course_name, co.group_label
                             FROM enrollments e
                             JOIN course_offerings co ON e.course_offering_id = co.id
                             JOIN courses c ON co.course_id = c.id
                            WHERE e.student_id = $1
                              AND e.course_offering_id = $2
                              AND e.status = ANY($3::text[])""",
                        student_id, item.id, list(ESTADOS_ACTIVOS),
                    )
                    if existente:
                        nombre = existente["course_name"]
                        if existente["group_label"]:
                            nombre += f" (Grupo {existente['group_label']})"
                        raise _RegistroInvalido(f"Ya tienes una matrícula activa en el curso {nombre}. "
                                                 f"Revisa tu selección.")

                    en_paquete = await db.fetchrow(
                        """SELECT c.name AS course_name, p.name AS package_name, co.group_label
                             FROM enrollments e
                             JOIN package_offerings po ON e.package_offering_id = po.id
                             JOIN packages p ON po.package_id = p.id
                             JOIN package_offering_courses poc ON poc.package_offering_id = po.id
                             JOIN course_offerings co ON poc.course_offering_id = co.id
                             JOIN courses c ON co.course_id = c.id
                            WHERE e.student_id = $1
                              AND e.status = ANY($2::text[])
                              AND co.id = $3""",
                        student_id, list(ESTADOS_ACTIVOS), item.id,
                    )
                    if en_paquete:
                        nombre = en_paquete["course_name"]
                        if en_paquete["group_label"]:
                            nombre += f" (Grupo {en_paquete['group_label']})"
                        raise _RegistroInvalido(
                            f"El curso {nombre} ya está incluido en el paquete "
                            f"«{en_paquete['package_name']}» en el que estás matriculado, "
                            f"por lo que no necesitas matricularte por separado.")

                else:  # package
                    existente = await db.fetchrow(
                        """SELECT p.name AS package_name, po.group_label
                             FROM enrollments e
                             JOIN package_offerings po ON e.package_offering_id = po.id
                             JOIN packages p ON po.package_id = p.id
                            WHERE e.student_id = $1
                              AND e.package_offering_id = $2
                              AND e.status = ANY($3::text[])""",
                        student_id, item.id, list(ESTADOS_ACTIVOS),
                    )
                    if existente:
                        nombre = existente["package_name"]
                        if existente["group_label"]:
                            nombre += f" (Grupo {existente['group_label']})"
                        raise _RegistroInvalido(f"Ya tienes una matrícula activa en el paquete {nombre}. "
                                                 f"Revisa tu selección.")

                    conflicto = await db.fetchrow(
                        """SELECT c.name AS course_name, co.group_label
                             FROM package_offering_courses poc
                             JOIN course_offerings co ON poc.course_offering_id = co.id
                             JOIN courses c ON co.course_id = c.id
                             JOIN enrollments e ON e.course_offering_id = co.id
                            WHERE poc.package_offering_id = $1
                              AND e.student_id = $2
                              AND e.status = ANY($3::text[])
                            LIMIT 1""",
                        item.id, student_id, list(ESTADOS_ACTIVOS),
                    )
                    if conflicto:
                        nombre = conflicto["course_name"]
                        if conflicto["group_label"]:
                            nombre += f" (Grupo {conflicto['group_label']})"
                        raise _RegistroInvalido(
                            f"Este paquete incluye el curso {nombre}, en el que ya estás "
                            f"matriculado de forma individual. Cancela esa matrícula "
                            f"antes de contratar el paquete.")

                libres = await _plazas_disponibles(db, tipo, item.id)
                if libres is not None and libres <= 0:
                    raise _RegistroInvalido("Una de las ofertas seleccionadas ya no tiene plazas disponibles.")

            # ---------- PASO 2: creación ----------
            creadas = []
            for item in data.items:
                tipo = item.type.value

                if tipo == "course":
                    oferta = await db.fetchrow(
                        """SELECT COALESCE(co.price_override, c.base_price) AS price
                             FROM course_offerings co
                             JOIN courses c ON co.course_id = c.id
                            WHERE co.id = $1""",
                        item.id,
                    )
                else:
                    oferta = await db.fetchrow(
                        """SELECT COALESCE(po.price_override, p.base_price) AS price
                             FROM package_offerings po
                             JOIN packages p ON po.package_id = p.id
                            WHERE po.id = $1""",
                        item.id,
                    )

                if oferta is None:
                    raise _RegistroInvalido("Una de las ofertas seleccionadas ya no está disponible. "
                                             "Actualiza la página e inténtalo de nuevo.")
                precio = oferta["price"]
                if precio is None or float(precio) <= 0:
                    raise _RegistroInvalido("Una de las ofertas seleccionadas no tiene un precio configurado. "
                                             "Comunícate con la administración.")

                if tipo == "course":
                    nueva = await db.fetchrow(
                        """INSERT INTO enrollments
                             (student_id, course_offering_id, enrollment_type, status)
                           VALUES ($1, $2, 'course', 'pendiente') RETURNING id""",
                        student_id, item.id,
                    )
                else:
                    nueva = await db.fetchrow(
                        """INSERT INTO enrollments
                             (student_id, package_offering_id, enrollment_type, status)
                           VALUES ($1, $2, 'package', 'pendiente') RETURNING id""",
                        student_id, item.id,
                    )

                enrollment_id = nueva["id"]
                await registrar_cambio_estado(
                    db, enrollment_id, None, "pendiente",
                    student_id, "student", "Alta de matrícula",
                )

                plan = await db.fetchrow(
                    """INSERT INTO payment_plans (enrollment_id, total_amount, installments)
                       VALUES ($1, $2, 1) RETURNING id""",
                    enrollment_id, precio,
                )
                vencimiento = date.today() + timedelta(days=7)
                cuota = await db.fetchrow(
                    """INSERT INTO installments
                         (payment_plan_id, installment_number, due_date, amount, status)
                       VALUES ($1, 1, $2, $3, 'pending') RETURNING id""",
                    plan["id"], vencimiento, precio,
                )

                creadas.append({
                    "enrollmentId": enrollment_id,
                    "payment_plan_id": plan["id"],
                    "installment_id": cuota["id"],
                    "amount": float(precio),
                    "due_date": vencimiento.isoformat(),
                })

            return {"message": "Matrículas registradas correctamente", "created": creadas}

    except _RegistroInvalido as e:
        return {"error": str(e)}
    except asyncpg.UniqueViolationError:
        return {"error": "Ya tienes una matrícula activa en uno de los cursos o paquetes "
                         "seleccionados. Actualiza la página; es posible que se haya "
                         "registrado desde otra sesión."}
    except asyncpg.ForeignKeyViolationError:
        return {"error": "Una de las ofertas seleccionadas ya no está disponible. "
                         "Actualiza la página e inténtalo de nuevo."}


# =====================================================================
# Cambios de estado
# =====================================================================

async def cancel_enrollment(
    student_id: int,
    enrollment_id: int,
    db: asyncpg.Connection,
    reason: Optional[str] = None,
):
    """
    C-03: el código original ejecutaba
        DELETE FROM enrollments WHERE id = $1
    y respondía «Matrícula cancelada correctamente». La fila desaparecía,
    junto con su plan de pago y sus cuotas. Consecuencias:
      · el estado 'cancelado' existía en el resto del sistema (filtros del
        frontend, condiciones SQL) pero jamás llegaba a producirse;
      · se perdía toda trazabilidad, en contra del RNF15;
      · el administrador no podía auditar quién se dio de baja ni cuándo.
    Ahora se conserva la fila y se cambia el estado.
    """
    async with db.transaction():
        enr = await db.fetchrow(
            "SELECT * FROM enrollments WHERE id = $1 AND student_id = $2",
            enrollment_id, student_id,
        )
        if not enr:
            return {"error": "Matrícula no encontrada"}

        if enr["status"] != "pendiente":
            etiqueta = ETIQUETAS_ESTADO.get(
                EnrollmentStatus(enr["status"]), enr["status"]
            ) if enr["status"] in {e.value for e in EnrollmentStatus} else enr["status"]
            return {"error": f"Solo puedes cancelar matrículas pendientes. "
                             f"Esta matrícula está en estado «{etiqueta}»."}

        con_pagos = await db.fetchval(
            """SELECT COUNT(*) FROM installments i
                 JOIN payment_plans pp ON i.payment_plan_id = pp.id
                WHERE pp.enrollment_id = $1
                  AND (i.status = 'paid' OR i.voucher_url IS NOT NULL)""",
            enrollment_id,
        )
        if con_pagos and con_pagos > 0:
            return {"error": "No puedes cancelar una matrícula que ya tiene un comprobante "
                             "de pago registrado. Comunícate con la administración."}

        await db.execute(
            """UPDATE enrollments
                  SET status = 'cancelado', cancelled_at = CURRENT_TIMESTAMP
                WHERE id = $1""",
            enrollment_id,
        )
        await registrar_cambio_estado(
            db, enrollment_id, enr["status"], "cancelado",
            student_id, "student", reason or "Cancelación solicitada por el estudiante",
        )

        propagadas = await _propagar_a_cursos_del_paquete(
            db, enr, "cancelado", student_id, "student",
            "Cancelación del paquete por el estudiante",
        )

        return {
            "message": "Matrícula cancelada correctamente",
            "enrollment_id": enrollment_id,
            "cursos_afectados": propagadas,
        }


async def update_enrollment_status(
    data: EnrollmentStatusUpdate,
    db: asyncpg.Connection,
    actor_id: Optional[int] = None,
    actor_rol: Optional[str] = None,
):
    """
    C-04 + C-06: valida la transición contra TRANSICIONES_VALIDAS.

    Antes, `data.status` era un `str` libre: un PUT con
    {"enrollment_id": 1, "status": "cualquier_cosa"} se persistía tal cual
    y dejaba la matrícula en un estado que ninguna pantalla sabía pintar.
    """
    async with db.transaction():
        enr = await db.fetchrow("SELECT * FROM enrollments WHERE id = $1", data.enrollment_id)
        if not enr:
            return {"error": "Matrícula no encontrada"}

        try:
            actual = EnrollmentStatus(enr["status"])
        except ValueError:
            return {"error": f"La matrícula tiene un estado no reconocido: «{enr['status']}»."}

        nuevo = data.status

        if actual == nuevo:
            return {"error": f"La matrícula ya se encuentra en estado "
                             f"«{ETIQUETAS_ESTADO[nuevo]}»."}

        permitidas = TRANSICIONES_VALIDAS.get(actual, set())
        if nuevo not in permitidas:
            if not permitidas:
                return {"error": f"«{ETIQUETAS_ESTADO[actual]}» es un estado final: "
                                 f"la matrícula ya no admite más cambios."}
            opciones = ", ".join(ETIQUETAS_ESTADO[e] for e in sorted(permitidas, key=lambda x: x.value))
            return {"error": f"No se puede pasar de «{ETIQUETAS_ESTADO[actual]}» a "
                             f"«{ETIQUETAS_ESTADO[nuevo]}». Transiciones permitidas: {opciones}."}

        if nuevo in (EnrollmentStatus.RECHAZADO, EnrollmentStatus.CANCELADO) and not data.reason:
            return {"error": "Debes indicar el motivo al rechazar o cancelar una matrícula."}

        # Aceptar exige el pago íntegro (regla ya existente, ahora explícita)
        if nuevo == EnrollmentStatus.ACEPTADO:
            pago = await db.fetchrow(
                """SELECT pp.total_amount,
                          COALESCE(SUM(CASE WHEN i.status = 'paid' THEN i.amount ELSE 0 END), 0)
                              AS total_pagado
                     FROM payment_plans pp
                     LEFT JOIN installments i ON i.payment_plan_id = pp.id
                    WHERE pp.enrollment_id = $1
                    GROUP BY pp.total_amount""",
                data.enrollment_id,
            )
            if not pago:
                return {"error": "Esta matrícula no tiene un plan de pago asociado."}
            if pago["total_pagado"] < pago["total_amount"]:
                falta = float(pago["total_amount"]) - float(pago["total_pagado"])
                return {"error": f"No se puede aceptar la matrícula: quedan S/ {falta:.2f} "
                                 f"por aprobar en las cuotas."}

            resultado = await aceptar_matricula(db, data.enrollment_id, actor_id, actor_rol)
            if "error" in resultado:
                return resultado
            if resultado["cursos_afectados"]:
                return {"message": f"Matrícula aceptada. Se sincronizaron "
                                   f"{resultado['cursos_afectados']} curso(s) del paquete."}
            return {"message": "Matrícula aceptada."}

        # Finalizar exige haber estado aceptada y que el ciclo haya terminado
        if nuevo == EnrollmentStatus.FINALIZADO:
            ciclo = await db.fetchrow(
                """SELECT cyc.end_date
                     FROM enrollments e
                     LEFT JOIN course_offerings  co  ON e.course_offering_id = co.id
                     LEFT JOIN package_offerings po  ON e.package_offering_id = po.id
                     LEFT JOIN cycles            cyc ON cyc.id = COALESCE(co.cycle_id, po.cycle_id)
                    WHERE e.id = $1""",
                data.enrollment_id,
            )
            if ciclo and ciclo["end_date"] and ciclo["end_date"] > date.today():
                return {"error": f"El ciclo termina el "
                                 f"{ciclo['end_date'].strftime('%d/%m/%Y')}; "
                                 f"la matrícula no puede finalizarse antes de esa fecha."}

        columna_fecha = {
            EnrollmentStatus.RECHAZADO: "rejected_at",
            EnrollmentStatus.CANCELADO: "cancelled_at",
            EnrollmentStatus.FINALIZADO: "finalized_at",
        }.get(nuevo)

        if columna_fecha:
            await db.execute(
                f"UPDATE enrollments SET status = $1, {columna_fecha} = CURRENT_TIMESTAMP WHERE id = $2",
                nuevo.value, data.enrollment_id,
            )
        else:
            await db.execute(
                "UPDATE enrollments SET status = $1 WHERE id = $2",
                nuevo.value, data.enrollment_id,
            )

        await registrar_cambio_estado(
            db, data.enrollment_id, actual.value, nuevo.value,
            actor_id, actor_rol, data.reason,
        )

        propagadas = 0
        if nuevo in (EnrollmentStatus.RECHAZADO, EnrollmentStatus.CANCELADO,
                     EnrollmentStatus.FINALIZADO):
            propagadas = await _propagar_a_cursos_del_paquete(
                db, enr, nuevo.value, actor_id, actor_rol, data.reason,
            )

        mensaje = f"Matrícula marcada como «{ETIQUETAS_ESTADO[nuevo]}»."
        if propagadas:
            mensaje += f" Se actualizaron también {propagadas} curso(s) del paquete."
        return {"message": mensaje}


async def delete_enrollment(enrollment_id: int, db: asyncpg.Connection,
                            actor_id: Optional[int] = None):
    """
    C-10: la versión original ejecutaba el DELETE a ciegas y siempre
    respondía «Matrícula eliminada correctamente», incluso con un id
    inexistente, y borraba matrículas con pagos ya aprobados.

    C-14: toda matrícula tiene, desde el alta, una fila en payment_plans (con
    su installment) y al menos una en enrollment_status_history — el DELETE
    de arriba violaba esa clave foránea en prácticamente todos los casos y
    caía en el 503 genérico de main.py en vez de borrar nada. Ahora se limpian
    las filas dependientes primero, dentro de una transacción.
    """
    enr = await db.fetchrow("SELECT id, status FROM enrollments WHERE id = $1", enrollment_id)
    if not enr:
        return {"error": "La matrícula indicada no existe."}

    pagados = await db.fetchval(
        """SELECT COUNT(*) FROM installments i
             JOIN payment_plans pp ON i.payment_plan_id = pp.id
            WHERE pp.enrollment_id = $1 AND i.status = 'paid'""",
        enrollment_id,
    )
    if pagados and pagados > 0:
        return {"error": "No se puede eliminar una matrícula con pagos aprobados. "
                         "Cámbiala a «Cancelada» para conservar el registro contable."}

    async with db.transaction():
        await db.execute(
            """DELETE FROM installments
                WHERE payment_plan_id IN (
                    SELECT id FROM payment_plans WHERE enrollment_id = $1
                )""",
            enrollment_id,
        )
        await db.execute("DELETE FROM payment_plans WHERE enrollment_id = $1", enrollment_id)
        await db.execute("DELETE FROM enrollment_status_history WHERE enrollment_id = $1", enrollment_id)
        await db.execute("DELETE FROM enrollments WHERE id = $1", enrollment_id)

    return {"message": "Matrícula eliminada correctamente"}
