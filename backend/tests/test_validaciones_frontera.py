"""
Pruebas de Caja Negra - Valor Límite y Clases de Equivalencia
Estrategia Pressman, Cap. 17 - Sección 2.3 (Análisis de Valor Límite)

Se ejercitan los validadores de los modelos Pydantic de Ciclos, Cursos y Ofertas
justo EN los bordes de cada partición (0, -0.01, +0.01, fin == inicio, ...), que
es donde históricamente se concentran los defectos.

Las pruebas marcadas con `xfail(strict=True)` describen el comportamiento
CORRECTO de defectos que siguen ABIERTOS en la rama. Cuando se corrija el
código, pytest reportará XPASS y obligará a convertirlas en pruebas de
regresión (misma mecánica que se usó con BG-C1..BG-C4 en
test_bugs_validacion.py).
"""
import sys
from pathlib import Path
from datetime import date

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.cycle import CycleCreate
from models.course import CourseCreate, CourseOfferingCreate


# Rango de fechas coherente reutilizado por los casos de ciclo
INICIO = date(2026, 3, 1)
FIN = date(2026, 7, 31)


def ciclo(**kwargs):
    """Construye un CycleCreate válido permitiendo sobreescribir un campo."""
    base = {
        "name": "Ciclo 2026-I",
        "start_date": INICIO,
        "end_date": FIN,
        "duration_months": 5,
    }
    base.update(kwargs)
    return CycleCreate(**base)


def oferta(**kwargs):
    base = {"course_id": 10, "cycle_id": 1, "group_label": "A"}
    base.update(kwargs)
    return CourseOfferingCreate(**base)


# ---------------------------------------------------------------------------
# base_price - fronteras de la partición "precio válido"
# ---------------------------------------------------------------------------
def test_precio_justo_bajo_cero_es_rechazado():
    """Límite inferior externo: -0.01 debe caer en la partición inválida."""
    with pytest.raises(ValidationError):
        CourseCreate(name="Álgebra", base_price=-0.01)


def test_precio_minimo_positivo_es_aceptado():
    """Límite inferior interno: 0.01 es el menor precio comercialmente válido."""
    assert CourseCreate(name="Álgebra", base_price=0.01).base_price == 0.01


@pytest.mark.xfail(
    strict=True,
    reason="BG-C7: la matriz (SEM-02) afirma que un precio en CERO se rechaza, "
           "pero el validador es 'v < 0', así que base_price=0 se acepta y "
           "permite matricular un curso gratuito por error de tipeo.",
)
def test_precio_cero_debe_ser_rechazado():
    """Valor límite ON-point: 0 no es un precio de venta legítimo."""
    with pytest.raises(ValidationError):
        CourseCreate(name="Álgebra", base_price=0)


def test_precio_no_numerico_es_rechazado():
    """Clase de equivalencia inválida: texto que no representa un número."""
    with pytest.raises(ValidationError):
        CourseCreate(name="Álgebra", base_price="gratis")


def test_precio_numerico_en_texto_se_convierte():
    """El formulario envía strings; Pydantic debe coercionarlos a float."""
    assert CourseCreate(name="Álgebra", base_price="150.50").base_price == 150.50


# ---------------------------------------------------------------------------
# duration_months - fronteras
# ---------------------------------------------------------------------------
def test_duracion_uno_es_aceptada():
    """Límite inferior interno: 1 mes es la duración mínima válida."""
    assert ciclo(duration_months=1).duration_months == 1


@pytest.mark.parametrize("valor", [0, -1])
def test_duracion_no_positiva_es_rechazada(valor):
    """ON-point (0) y OFF-point (-1) de la partición inválida."""
    with pytest.raises(ValidationError):
        ciclo(duration_months=valor)


@pytest.mark.xfail(
    strict=True,
    reason="BG-C10: no se valida coherencia entre duration_months y el rango de "
           "fechas. Un ciclo del 01/03 al 31/07 (5 meses) acepta "
           "duration_months=99, y ese dato alimenta los cálculos de cuotas.",
)
def test_duracion_incoherente_con_las_fechas_debe_rechazarse():
    with pytest.raises(ValidationError):
        ciclo(duration_months=99)


# ---------------------------------------------------------------------------
# start_date / end_date - fronteras del invariante fin > inicio
# ---------------------------------------------------------------------------
def test_fin_igual_a_inicio_es_rechazado():
    """ON-point del invariante: un ciclo de duración cero no es válido."""
    with pytest.raises(ValidationError):
        ciclo(start_date=INICIO, end_date=INICIO)


def test_fin_un_dia_despues_de_inicio_es_aceptado():
    """OFF-point interno: el mínimo rango estrictamente positivo se acepta."""
    c = ciclo(start_date=date(2026, 3, 1), end_date=date(2026, 3, 2), duration_months=1)
    assert c.end_date > c.start_date


def test_fecha_con_formato_invalido_es_rechazada():
    with pytest.raises(ValidationError):
        ciclo(start_date="01-03-2026")  # se espera ISO YYYY-MM-DD


# ---------------------------------------------------------------------------
# name - clases de equivalencia de la cadena obligatoria
# ---------------------------------------------------------------------------
def test_nombre_ausente_es_rechazado():
    """Equivale al caso CF-05 del script de función, a nivel de modelo."""
    with pytest.raises(ValidationError):
        CycleCreate(start_date=INICIO, end_date=FIN, duration_months=5)


@pytest.mark.xfail(
    strict=True,
    reason="BG-C8: 'name' es str sin min_length, así que la cadena vacía pasa la "
           "validación y crea un ciclo sin nombre en la tabla de gestión.",
)
def test_nombre_vacio_debe_ser_rechazado():
    with pytest.raises(ValidationError):
        ciclo(name="")


@pytest.mark.xfail(
    strict=True,
    reason="BG-C8: tampoco se hace strip(), así que '   ' pasa como nombre "
           "válido y se ve como una fila en blanco en la UI.",
)
def test_nombre_solo_espacios_debe_ser_rechazado():
    with pytest.raises(ValidationError):
        CourseCreate(name="   ", base_price=100.0)


# ---------------------------------------------------------------------------
# status - catálogo cerrado de estados
# ---------------------------------------------------------------------------
def test_status_por_defecto_es_open():
    """La UI colorea chips para open / in_progress / closed."""
    assert ciclo().status == "open"


@pytest.mark.parametrize("estado", ["open", "in_progress", "closed"])
def test_estados_del_catalogo_son_aceptados(estado):
    assert ciclo(status=estado).status == estado


@pytest.mark.xfail(
    strict=True,
    reason="BG-C9: 'status' es un str libre sin Enum ni validador. Un estado "
           "desconocido se persiste y la UI cae en el 'default' de "
           "getStatusColor(), además de romper GET /cycles/active que filtra "
           "por status = 'open'.",
)
def test_status_fuera_del_catalogo_debe_ser_rechazado():
    with pytest.raises(ValidationError):
        ciclo(status="banana")


# ---------------------------------------------------------------------------
# CourseOffering - campos numéricos sin validador alguno
# ---------------------------------------------------------------------------
def test_oferta_minima_valida_se_acepta():
    o = oferta(teacher_id=None, price_override=None, capacity=None)
    assert o.course_id == 10 and o.cycle_id == 1


@pytest.mark.xfail(
    strict=True,
    reason="BG-C11: CourseOfferingCreate no valida price_override, de modo que "
           "un precio negativo sobreescribe el base_price del curso y genera "
           "deudas negativas en la matrícula.",
)
def test_price_override_negativo_debe_ser_rechazado():
    with pytest.raises(ValidationError):
        oferta(price_override=-500.0)


@pytest.mark.xfail(
    strict=True,
    reason="BG-C12: capacity no tiene validador. Una capacidad 0 o negativa "
           "deja un grupo publicado en el que nadie puede matricularse.",
)
@pytest.mark.parametrize("cupo", [0, -10])
def test_capacity_no_positiva_debe_ser_rechazada(cupo):
    with pytest.raises(ValidationError):
        oferta(capacity=cupo)


def test_oferta_sin_curso_ni_ciclo_es_rechazada():
    """course_id y cycle_id son obligatorios: sin ellos la oferta no existe."""
    with pytest.raises(ValidationError):
        CourseOfferingCreate(group_label="A")
