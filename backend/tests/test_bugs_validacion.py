"""
Pruebas de REGRESIÓN de defectos corregidos (Bitácora de errores - Bug Log)
Estrategia Pressman, Cap. 17.

Estas pruebas describen el comportamiento CORRECTO. Antes fallaban (estaban marcadas
xfail porque el sistema tenía los defectos BG-C1/C2/C3/C4); tras corregir los bugs,
ahora PASAN, demostrando que las correcciones funcionan y evitando regresiones futuras.
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
from models.cycle import CycleCreate
from models.course import CourseCreate


# ---------------------------------------------------------------------------
# BG-C1: create_cycle ahora valida que end_date > start_date y duración > 0
# ---------------------------------------------------------------------------
def test_ciclo_rechaza_fecha_fin_anterior_a_inicio():
    with pytest.raises(ValidationError):
        CycleCreate(
            name="Ciclo inválido",
            start_date=date(2026, 7, 31),
            end_date=date(2026, 3, 1),   # anterior al inicio
            duration_months=5,
        )


def test_ciclo_rechaza_duracion_no_positiva():
    with pytest.raises(ValidationError):
        CycleCreate(
            name="Ciclo inválido",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 7, 31),
            duration_months=0,   # no tiene sentido
        )


def test_ciclo_valido_se_acepta():
    # Caso de control: un ciclo coherente NO debe lanzar error.
    c = CycleCreate(
        name="Ciclo 2026-I",
        start_date=date(2026, 3, 1),
        end_date=date(2026, 7, 31),
        duration_months=5,
    )
    assert c.duration_months == 5


# ---------------------------------------------------------------------------
# BG-C3: create_course ahora rechaza base_price negativo
# ---------------------------------------------------------------------------
def test_curso_rechaza_precio_negativo():
    with pytest.raises(ValidationError):
        CourseCreate(name="Álgebra", base_price=-50.0)


def test_curso_precio_valido_se_acepta():
    c = CourseCreate(name="Álgebra", base_price=150.0)
    assert c.base_price == 150.0


# ---------------------------------------------------------------------------
# BG-C2: borrar un id inexistente ahora devuelve 404 (no un falso positivo)
# ---------------------------------------------------------------------------
async def test_delete_curso_inexistente_avisa_no_encontrado():
    db = AsyncMock()
    db.fetchval.return_value = 0          # sin ofertas asociadas
    db.execute.return_value = "DELETE 0"  # ninguna fila borrada

    with pytest.raises(HTTPException) as exc:
        await courseController.delete_course(99999, db)

    assert exc.value.status_code == 404
    assert "no encontrado" in exc.value.detail.lower()


# ---------------------------------------------------------------------------
# BG-C4: no se puede borrar un ciclo/curso con dependencias (devuelve 409)
# ---------------------------------------------------------------------------
async def test_delete_ciclo_con_ofertas_es_bloqueado():
    db = AsyncMock()
    db.fetchval.return_value = 3  # el ciclo tiene 3 ofertas asociadas

    with pytest.raises(HTTPException) as exc:
        await cycleController.delete_cycle(1, db)

    assert exc.value.status_code == 409
    db.execute.assert_not_awaited()  # nunca llega a ejecutar el DELETE


async def test_delete_curso_con_ofertas_es_bloqueado():
    db = AsyncMock()
    db.fetchval.return_value = 2  # el curso tiene 2 ofertas asociadas

    with pytest.raises(HTTPException) as exc:
        await courseController.delete_course(1, db)

    assert exc.value.status_code == 409
    db.execute.assert_not_awaited()
