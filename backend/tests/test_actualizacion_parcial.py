"""
Pruebas de Unidad (Caja Blanca) - Rutas de ACTUALIZACIÓN (PUT)
Estrategia Pressman, Cap. 17 - Sección 2.1

La matriz original cubre la creación y el borrado con bastante detalle, pero de
la actualización sólo prueba el camino feliz (CF-03 y CF-08). Aquí se ejercitan
los caminos que quedaban sin recorrer: id inexistente, actualización parcial que
rompe invariantes y construcción dinámica del SET de la sentencia SQL.

Las pruebas `xfail(strict=True)` describen defectos ABIERTOS.
"""
import sys
from pathlib import Path
from datetime import date
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).parent.parent))

import controllers.cycleController as cycleController
import controllers.courseController as courseController
from models.cycle import CycleUpdate
from models.course import CourseUpdate, CourseOfferingUpdate


# ---------------------------------------------------------------------------
# BG-C13: PUT sobre un id inexistente responde "actualizado correctamente"
#
# BG-C2 arregló este falso positivo en los DELETE (comprobando el "DELETE 0"
# que devuelve asyncpg), pero los UPDATE nunca revisan el "UPDATE 0".
# ---------------------------------------------------------------------------
@pytest.mark.xfail(
    strict=True,
    reason="BG-C13: update_cycle ignora el resultado 'UPDATE 0' de asyncpg y "
           "responde éxito aunque el ciclo no exista (asimetría con BG-C2, ya "
           "corregido en delete_cycle).",
)
async def test_update_cycle_inexistente_debe_devolver_404():
    db = AsyncMock()
    db.execute.return_value = "UPDATE 0"  # ninguna fila afectada

    with pytest.raises(HTTPException) as exc:
        await cycleController.update_cycle(99999, CycleUpdate(name="Fantasma"), db)

    assert exc.value.status_code == 404


@pytest.mark.xfail(
    strict=True,
    reason="BG-C13: mismo falso positivo en update_course; el frontend muestra "
           "'Curso actualizado correctamente' sin que se haya tocado nada.",
)
async def test_update_course_inexistente_debe_devolver_404():
    db = AsyncMock()
    db.execute.return_value = "UPDATE 0"

    with pytest.raises(HTTPException) as exc:
        await courseController.update_course(99999, CourseUpdate(base_price=1.0), db)

    assert exc.value.status_code == 404


@pytest.mark.xfail(
    strict=True,
    reason="BG-C13: y también en update_course_offering.",
)
async def test_update_offering_inexistente_debe_devolver_404():
    db = AsyncMock()
    db.execute.return_value = "UPDATE 0"

    with pytest.raises(HTTPException) as exc:
        await courseController.update_course_offering(
            99999, CourseOfferingUpdate(capacity=40), db
        )

    assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# BG-C14: la actualización parcial puede invertir el invariante fin > inicio
#
# CycleUpdate.end_after_start sólo valida cuando AMBAS fechas viajan en el
# cuerpo. Enviando una sola fecha se elude el invariante que CF-04 protege en
# la creación.
# ---------------------------------------------------------------------------
def test_update_cycle_con_ambas_fechas_invertidas_es_rechazado():
    """Camino cubierto: las dos fechas presentes sí se validan entre sí."""
    with pytest.raises(ValidationError):
        CycleUpdate(start_date=date(2026, 7, 31), end_date=date(2026, 3, 1))


def test_update_cycle_con_ambas_fechas_iguales_es_rechazado():
    with pytest.raises(ValidationError):
        CycleUpdate(start_date=date(2026, 3, 1), end_date=date(2026, 3, 1))


@pytest.mark.xfail(
    strict=True,
    reason="BG-C14: enviando SOLO end_date no hay nada contra lo que comparar y "
           "el modelo la acepta; el ciclo queda con fin anterior a inicio, el "
           "mismo estado que CF-04 impide al crear. La validación debe hacerse "
           "en el controlador contra las fechas ya guardadas.",
)
async def test_update_cycle_solo_end_date_anterior_al_inicio_guardado_debe_rechazarse():
    db = AsyncMock()
    # Fechas actualmente persistidas para el ciclo 1
    db.fetchrow.return_value = {
        "id": 1,
        "start_date": date(2026, 3, 1),
        "end_date": date(2026, 7, 31),
    }
    db.execute.return_value = "UPDATE 1"

    with pytest.raises(HTTPException) as exc:
        await cycleController.update_cycle(
            1, CycleUpdate(end_date=date(2020, 1, 1)), db
        )

    assert exc.value.status_code in (400, 422)


@pytest.mark.xfail(
    strict=True,
    reason="BG-C14 (variante): enviando SOLO start_date posterior al end_date "
           "guardado se produce la misma inconsistencia.",
)
async def test_update_cycle_solo_start_date_posterior_al_fin_guardado_debe_rechazarse():
    db = AsyncMock()
    db.fetchrow.return_value = {
        "id": 1,
        "start_date": date(2026, 3, 1),
        "end_date": date(2026, 7, 31),
    }
    db.execute.return_value = "UPDATE 1"

    with pytest.raises(HTTPException) as exc:
        await cycleController.update_cycle(
            1, CycleUpdate(start_date=date(2027, 1, 1)), db
        )

    assert exc.value.status_code in (400, 422)


# ---------------------------------------------------------------------------
# Construcción dinámica del SET (caja blanca sobre el bucle de campos)
# ---------------------------------------------------------------------------
async def test_update_cycle_solo_actualiza_los_campos_enviados():
    """exclude_unset debe dejar fuera los campos que el formulario no tocó."""
    db = AsyncMock()
    db.execute.return_value = "UPDATE 1"

    await cycleController.update_cycle(4, CycleUpdate(name="Ciclo 2026-II"), db)

    query, *valores = db.execute.await_args.args
    assert query.count("=") == 2          # un campo del SET + el WHERE id
    assert "name = $1" in query
    assert "status" not in query          # no se pisa el estado actual
    assert valores == ["Ciclo 2026-II", 4]


async def test_update_cycle_numera_los_placeholders_en_orden():
    """Un desajuste entre $n y el orden de los valores corrompería filas."""
    db = AsyncMock()
    db.execute.return_value = "UPDATE 1"

    data = CycleUpdate(
        name="Ciclo 2026-II",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 12, 20),
        duration_months=5,
        status="in_progress",
    )
    await cycleController.update_cycle(9, data, db)

    query, *valores = db.execute.await_args.args
    for posicion, campo in enumerate(data.model_dump(exclude_unset=True), start=1):
        assert f"{campo} = ${posicion}" in query
    assert query.endswith(f"WHERE id = ${len(valores)}")
    assert valores[-1] == 9


async def test_update_offering_permite_desasignar_el_profesor():
    """None explícito debe viajar al SET, no confundirse con 'campo no enviado'."""
    db = AsyncMock()
    db.execute.return_value = "UPDATE 1"

    await courseController.update_course_offering(
        7, CourseOfferingUpdate(teacher_id=None), db
    )

    query, *valores = db.execute.await_args.args
    assert "teacher_id = $1" in query
    assert valores == [None, 7]


async def test_update_offering_sin_campos_no_ejecuta_query():
    """Guardar un formulario sin cambios no debe llegar a la BD."""
    db = AsyncMock()

    result = await courseController.update_course_offering(
        20, CourseOfferingUpdate(), db
    )

    assert result["message"] == "No hay campos para actualizar"
    db.execute.assert_not_awaited()
