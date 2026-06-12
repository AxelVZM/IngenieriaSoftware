"""
Pruebas que EVIDENCIAN defectos (Bitácora de errores - Bug Log)
Estrategia Pressman, Cap. 17: "el éxito del testing se evidencia en el
descubrimiento de defectos".

Estas pruebas describen el comportamiento CORRECTO esperado. Como el sistema
todavía NO lo cumple, se marcan con @pytest.mark.xfail (fallo esperado):
- Aparecen como 'xfailed' (amarillo), NO rompen el suite -> sigue en verde.
- Cuando el bug se corrija, pasarán a 'xpassed', señalando que ya está resuelto.

Mapea con la Bitácora de Errores: BG-C1, BG-C2, BG-C3.
"""
import sys
from pathlib import Path
from datetime import date
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).parent.parent))

import controllers.courseController as courseController
from models.cycle import CycleCreate
from models.course import CourseCreate


# ---------------------------------------------------------------------------
# BG-C1: create_cycle no valida que end_date > start_date
# ---------------------------------------------------------------------------
@pytest.mark.xfail(
    reason="BG-C1: el modelo no valida que la fecha de fin sea posterior a la de inicio",
    strict=False,
)
def test_ciclo_rechaza_fecha_fin_anterior_a_inicio():
    # Un ciclo con fin ANTES del inicio debería ser rechazado.
    with pytest.raises(ValidationError):
        CycleCreate(
            name="Ciclo inválido",
            start_date=date(2026, 7, 31),
            end_date=date(2026, 3, 1),   # anterior al inicio
            duration_months=5,
        )


@pytest.mark.xfail(
    reason="BG-C1: el modelo no valida que duration_months sea > 0",
    strict=False,
)
def test_ciclo_rechaza_duracion_no_positiva():
    with pytest.raises(ValidationError):
        CycleCreate(
            name="Ciclo inválido",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 7, 31),
            duration_months=0,   # no tiene sentido
        )


# ---------------------------------------------------------------------------
# BG-C3: create_course acepta base_price negativo
# ---------------------------------------------------------------------------
@pytest.mark.xfail(
    reason="BG-C3: el modelo acepta precios negativos (no valida base_price >= 0)",
    strict=False,
)
def test_curso_rechaza_precio_negativo():
    with pytest.raises(ValidationError):
        CourseCreate(name="Álgebra", base_price=-50.0)


# ---------------------------------------------------------------------------
# BG-C2: delete_course no verifica existencia (falso positivo)
# ---------------------------------------------------------------------------
@pytest.mark.xfail(
    reason="BG-C2: borrar un id inexistente responde 'eliminado correctamente'",
    strict=False,
)
async def test_delete_curso_inexistente_deberia_avisar_no_encontrado():
    db = AsyncMock()
    # asyncpg devuelve el status del comando; 'DELETE 0' = ninguna fila borrada
    db.execute.return_value = "DELETE 0"

    result = await courseController.delete_course(99999, db)

    # Lo correcto sería avisar que no existe, no confirmar el borrado.
    assert "no encontrado" in result["message"].lower()
