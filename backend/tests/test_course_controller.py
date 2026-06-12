"""
Pruebas de Unidad (Caja Blanca) - Controlador de Cursos y Ofertas
Estrategia Pressman, Cap. 17 - Sección 2.1

La conexión a la base de datos (asyncpg) se reemplaza por un mock (AsyncMock).
"""
import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import controllers.courseController as courseController
from models.course import (
    CourseCreate,
    CourseUpdate,
    CourseOfferingCreate,
    CourseOfferingUpdate,
)


# ---------------------------------------------------------------------------
# create_course
# ---------------------------------------------------------------------------
async def test_create_course_devuelve_id_y_mensaje():
    db = AsyncMock()
    db.fetchrow.return_value = {"id": 10}

    data = CourseCreate(name="Álgebra", description="Curso base", base_price=150.0)

    result = await courseController.create_course(data, db)

    assert result["id"] == 10
    assert result["message"] == "Curso creado exitosamente"
    db.fetchrow.assert_awaited_once()


# ---------------------------------------------------------------------------
# update_course
# ---------------------------------------------------------------------------
async def test_update_course_sin_campos_no_ejecuta_query():
    db = AsyncMock()

    result = await courseController.update_course(1, CourseUpdate(), db)

    assert result["message"] == "No hay campos para actualizar"
    db.execute.assert_not_awaited()


async def test_update_course_con_campos_ejecuta_update():
    db = AsyncMock()

    result = await courseController.update_course(5, CourseUpdate(base_price=200.0), db)

    assert result["message"] == "Curso actualizado correctamente"
    db.execute.assert_awaited_once()
    args = db.execute.await_args.args
    assert "UPDATE courses SET" in args[0]
    assert args[-1] == 5


# ---------------------------------------------------------------------------
# delete_course
# ---------------------------------------------------------------------------
async def test_delete_course_ejecuta_delete_con_id():
    db = AsyncMock()
    db.fetchval.return_value = 0          # sin ofertas asociadas (BG-C4)
    db.execute.return_value = "DELETE 1"  # se borró 1 fila (BG-C2)

    result = await courseController.delete_course(8, db)

    assert result["message"] == "Curso eliminado correctamente"
    db.execute.assert_awaited_once()
    args = db.execute.await_args.args
    assert "DELETE FROM courses" in args[0]
    assert args[1] == 8


# ---------------------------------------------------------------------------
# create_course_offering
# ---------------------------------------------------------------------------
async def test_create_offering_liga_curso_y_ciclo():
    db = AsyncMock()
    db.fetchrow.return_value = {"id": 20}

    data = CourseOfferingCreate(
        course_id=10,
        cycle_id=1,
        group_label="A",
        teacher_id=3,
        price_override=None,
        capacity=30,
    )

    result = await courseController.create_course_offering(data, db)

    assert result["id"] == 20
    assert result["message"] == "Oferta de curso creada exitosamente"
    db.fetchrow.assert_awaited_once()


# ---------------------------------------------------------------------------
# get_course_offerings
# ---------------------------------------------------------------------------
async def test_get_course_offerings_retorna_lista():
    db = AsyncMock()
    db.fetch.return_value = [
        {"id": 20, "course_name": "Álgebra", "group_label": "A"},
        {"id": 21, "course_name": "Álgebra", "group_label": "B"},
    ]

    result = await courseController.get_course_offerings(1, db)

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["course_name"] == "Álgebra"


# ---------------------------------------------------------------------------
# update_course_offering
# ---------------------------------------------------------------------------
async def test_update_offering_con_campos_ejecuta_update():
    db = AsyncMock()

    result = await courseController.update_course_offering(
        20, CourseOfferingUpdate(capacity=40), db
    )

    assert result["message"] == "Oferta actualizada correctamente"
    db.execute.assert_awaited_once()
    args = db.execute.await_args.args
    assert "UPDATE course_offerings SET" in args[0]
    assert args[-1] == 20


# ---------------------------------------------------------------------------
# get_all_courses (incluye ofertas + horarios anidados)
# ---------------------------------------------------------------------------
async def test_get_all_courses_anida_ofertas_y_horarios():
    db = AsyncMock()
    # 1ra llamada: cursos | 2da: ofertas del curso | 3ra: horarios de la oferta
    db.fetch.side_effect = [
        [{"id": 10, "name": "Álgebra"}],          # courses
        [{"id": 20, "course_id": 10}],            # offerings del curso 10
        [{"id": 100, "course_offering_id": 20}],  # schedules de la oferta 20
    ]

    result = await courseController.get_all_courses(db)

    assert len(result) == 1
    curso = result[0]
    assert curso["name"] == "Álgebra"
    assert len(curso["offerings"]) == 1
    assert len(curso["offerings"][0]["schedules"]) == 1
