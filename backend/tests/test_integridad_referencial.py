"""
Pruebas de Integración de Componentes - Integridad referencial y cascadas
Estrategia Pressman, Cap. 17 - Sección 2.2

La matriz cubre la cascada "curso con ofertas" (CF-12). Aquí se completa el resto
de la malla de dependencias del módulo:

    cycles ──┐
             ├─→ course_offerings ──→ enrollments
    courses ─┘                   └─→ schedules

Se verifica que cada eliminación consulte a sus dependientes ANTES de borrar, que
un id inexistente devuelva 404 y qué ocurre cuando la BD rechaza una clave ajena.
"""
import sys
from pathlib import Path
from unittest.mock import AsyncMock

import asyncpg
import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).parent.parent))

import controllers.cycleController as cycleController
import controllers.courseController as courseController
from models.course import CourseOfferingCreate


# ---------------------------------------------------------------------------
# 404 al borrar un id inexistente (BG-C2) — faltaba el lado de ciclos y ofertas
# ---------------------------------------------------------------------------
async def test_delete_cycle_inexistente_devuelve_404():
    db = AsyncMock()
    db.fetchval.return_value = 0          # sin ofertas asociadas
    db.execute.return_value = "DELETE 0"  # ninguna fila borrada

    with pytest.raises(HTTPException) as exc:
        await cycleController.delete_cycle(99999, db)

    assert exc.value.status_code == 404
    assert "no encontrado" in exc.value.detail.lower()


async def test_delete_offering_inexistente_devuelve_404():
    db = AsyncMock()
    db.fetchval.return_value = 0
    db.execute.return_value = "DELETE 0"

    with pytest.raises(HTTPException) as exc:
        await courseController.delete_course_offering(99999, db)

    assert exc.value.status_code == 404
    assert "no encontrada" in exc.value.detail.lower()


# ---------------------------------------------------------------------------
# 409 al borrar algo con dependientes (BG-C4) — faltaba oferta con matrículas
# ---------------------------------------------------------------------------
async def test_delete_offering_con_matriculas_es_bloqueado():
    """Borrar una oferta con alumnos dentro los dejaría sin grupo ni horario."""
    db = AsyncMock()
    db.fetchval.return_value = 5  # 5 matrículas asociadas

    with pytest.raises(HTTPException) as exc:
        await courseController.delete_course_offering(20, db)

    assert exc.value.status_code == 409
    assert "matrícula" in exc.value.detail.lower()
    db.execute.assert_not_awaited()  # no llega al DELETE


async def test_delete_offering_sin_matriculas_se_elimina():
    """Caso de control: la limpieza normal (usada por CF-11) sigue funcionando."""
    db = AsyncMock()
    db.fetchval.return_value = 0
    db.execute.return_value = "DELETE 1"

    result = await courseController.delete_course_offering(20, db)

    assert result["message"] == "Oferta eliminada correctamente"
    query, offering_id = db.execute.await_args.args
    assert "DELETE FROM course_offerings" in query
    assert offering_id == 20


# ---------------------------------------------------------------------------
# El chequeo de dependencias debe ir contra la tabla y el id correctos
# ---------------------------------------------------------------------------
async def test_delete_cycle_consulta_ofertas_del_ciclo_indicado():
    """Un WHERE mal escrito dejaría pasar borrados peligrosos (falso 0)."""
    db = AsyncMock()
    db.fetchval.return_value = 0
    db.execute.return_value = "DELETE 1"

    await cycleController.delete_cycle(42, db)

    query, cycle_id = db.fetchval.await_args.args
    assert "FROM course_offerings" in query
    assert "cycle_id = $1" in query
    assert cycle_id == 42


async def test_delete_course_consulta_ofertas_del_curso_indicado():
    db = AsyncMock()
    db.fetchval.return_value = 0
    db.execute.return_value = "DELETE 1"

    await courseController.delete_course(8, db)

    query, course_id = db.fetchval.await_args.args
    assert "FROM course_offerings" in query
    assert "course_id = $1" in query
    assert course_id == 8


async def test_delete_offering_consulta_matriculas_de_la_oferta_indicada():
    db = AsyncMock()
    db.fetchval.return_value = 0
    db.execute.return_value = "DELETE 1"

    await courseController.delete_course_offering(20, db)

    query, offering_id = db.fetchval.await_args.args
    assert "FROM enrollments" in query
    assert "course_offering_id = $1" in query
    assert offering_id == 20


@pytest.mark.xfail(
    strict=True,
    reason="BG-C17: delete_course_offering sólo mira enrollments, no schedules. "
           "Si la oferta tiene horarios y la FK de schedules no es ON DELETE "
           "CASCADE, el DELETE explota como 500 en vez de un 409 explicable.",
)
async def test_delete_offering_tambien_verifica_sus_horarios():
    db = AsyncMock()
    db.fetchval.return_value = 0
    db.execute.return_value = "DELETE 1"

    await courseController.delete_course_offering(20, db)

    consultas = [c.args[0] for c in db.fetchval.await_args_list]
    assert any("FROM schedules" in q for q in consultas)


# ---------------------------------------------------------------------------
# BG-C15: claves ajenas inexistentes al crear una oferta
# ---------------------------------------------------------------------------
@pytest.mark.xfail(
    strict=True,
    reason="BG-C15: create_course_offering inserta sin comprobar que course_id y "
           "cycle_id existan. La ForeignKeyViolationError de asyncpg sube sin "
           "capturar y FastAPI la traduce a un 500 con traza, en lugar de un "
           "400/404 que el frontend pueda mostrar.",
)
async def test_crear_oferta_con_curso_inexistente_devuelve_error_de_cliente():
    db = AsyncMock()
    db.fetchrow.side_effect = asyncpg.exceptions.ForeignKeyViolationError(
        'insert or update on table "course_offerings" violates foreign key constraint'
    )

    with pytest.raises(HTTPException) as exc:
        await courseController.create_course_offering(
            CourseOfferingCreate(course_id=999999, cycle_id=1, group_label="A"), db
        )

    assert exc.value.status_code in (400, 404, 409)


@pytest.mark.xfail(
    strict=True,
    reason="BG-C18: tampoco se comprueba la unicidad de (course_id, cycle_id, "
           "group_label); el mismo curso puede publicarse dos veces con el "
           "grupo 'A' en el mismo ciclo y los alumnos ven duplicados.",
)
async def test_crear_oferta_duplicada_en_el_mismo_ciclo_es_rechazada():
    db = AsyncMock()
    db.fetchrow.return_value = {"id": 21}
    db.fetchval.return_value = 1  # ya existe una oferta idéntica

    with pytest.raises(HTTPException) as exc:
        await courseController.create_course_offering(
            CourseOfferingCreate(course_id=10, cycle_id=1, group_label="A"), db
        )

    assert exc.value.status_code == 409


# ---------------------------------------------------------------------------
# Lectura de ofertas por ciclo
# ---------------------------------------------------------------------------
async def test_get_course_offerings_de_ciclo_sin_ofertas_retorna_lista_vacia():
    """La UI itera el resultado: debe ser [] y nunca None."""
    db = AsyncMock()
    db.fetch.return_value = []

    result = await courseController.get_course_offerings(999, db)

    assert result == []


async def test_get_all_courses_incluye_cursos_sin_ofertas():
    """Un curso recién creado (CF-07) debe listarse con offerings vacío."""
    db = AsyncMock()
    db.fetch.side_effect = [
        [{"id": 10, "name": "Álgebra"}, {"id": 11, "name": "Química"}],
        [{"id": 20, "course_id": 10}],            # sólo Álgebra tiene oferta
        [],                                      # ningún horario
    ]

    result = await courseController.get_all_courses(db)

    por_nombre = {c["name"]: c for c in result}
    assert por_nombre["Álgebra"]["offerings"] != []
    assert por_nombre["Química"]["offerings"] == []
    assert por_nombre["Álgebra"]["offerings"][0]["schedules"] == []


async def test_get_all_courses_no_mezcla_horarios_entre_ofertas():
    """Regresión de BG-C6: el agrupado en memoria no debe cruzar los horarios."""
    db = AsyncMock()
    db.fetch.side_effect = [
        [{"id": 10, "name": "Álgebra"}],
        [{"id": 20, "course_id": 10}, {"id": 21, "course_id": 10}],
        [
            {"id": 100, "course_offering_id": 20},
            {"id": 101, "course_offering_id": 21},
            {"id": 102, "course_offering_id": 21},
        ],
    ]

    result = await courseController.get_all_courses(db)

    ofertas = {o["id"]: o for o in result[0]["offerings"]}
    assert [s["id"] for s in ofertas[20]["schedules"]] == [100]
    assert [s["id"] for s in ofertas[21]["schedules"]] == [101, 102]


async def test_get_all_courses_hace_solo_tres_consultas():
    """Regresión de BG-C6: 3 consultas fijas, sin N+1 por curso u oferta."""
    db = AsyncMock()
    db.fetch.side_effect = [
        [{"id": 10, "name": "Álgebra"}, {"id": 11, "name": "Química"}],
        [{"id": 20, "course_id": 10}, {"id": 21, "course_id": 11}],
        [{"id": 100, "course_offering_id": 20}],
    ]

    await courseController.get_all_courses(db)

    assert db.fetch.await_count == 3


# ---------------------------------------------------------------------------
# BG-C16: unicidad del ciclo activo
# ---------------------------------------------------------------------------
async def test_get_active_cycle_toma_el_mas_reciente_de_los_abiertos():
    """Documenta la regla vigente: ORDER BY start_date DESC LIMIT 1."""
    db = AsyncMock()
    db.fetchrow.return_value = {"id": 7, "name": "Ciclo 2026-II", "status": "open"}

    result = await cycleController.get_active_cycle(db)

    query = db.fetchrow.await_args.args[0]
    assert "status = 'open'" in query
    assert "ORDER BY start_date DESC" in query and "LIMIT 1" in query
    assert result["id"] == 7


@pytest.mark.xfail(
    strict=True,
    reason="BG-C16: nada impide tener dos ciclos en 'open' a la vez. "
           "GET /cycles/active elige uno silenciosamente con LIMIT 1, así que "
           "las matrículas pueden caer en el ciclo equivocado.",
)
async def test_crear_segundo_ciclo_abierto_es_rechazado():
    db = AsyncMock()
    db.fetchval.return_value = 1  # ya hay un ciclo abierto
    db.fetchrow.return_value = {"id": 2}

    from datetime import date
    from models.cycle import CycleCreate

    with pytest.raises(HTTPException) as exc:
        await cycleController.create_cycle(
            CycleCreate(
                name="Segundo ciclo abierto",
                start_date=date(2026, 8, 1),
                end_date=date(2026, 12, 20),
                duration_months=5,
                status="open",
            ),
            db,
        )

    assert exc.value.status_code == 409
