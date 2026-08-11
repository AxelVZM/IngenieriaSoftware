"""
Pruebas del manejador global de errores 422.

El manejador arma el mensaje que termina viendo el usuario en los formularios
de cursos, ciclos, ofertas y horarios. Nombra los campos con su identificador
interno (`base_price`, `duration_months`), que es correcto para el registro y
para el cliente que quiera reaccionar campo por campo, pero **no** es lo que se
debe mostrar en pantalla. Por eso además del texto ya armado tiene que enviar
`errors`, con el campo y el mensaje por separado, para que el frontend lo
sustituya por la etiqueta del formulario.

Sin esa parte estructurada el frontend no tiene de dónde sacar el nombre del
campo y no le queda más remedio que enseñar el de la variable, que es
exactamente el defecto que estas pruebas impiden reintroducir.
"""

import json

import pytest
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

# Importar `main` arrastra las rutas y el middleware de autenticación, que
# exige un JWT_SECRET; conftest.py se encarga de que exista uno.
import main
from models.course import CourseCreate, CourseOfferingCreate, ScheduleCreate
from models.cycle import CycleCreate

pytestmark = pytest.mark.asyncio


def _errores_de(modelo, **datos):
    """Ejecuta el modelo con datos inválidos y devuelve los errores de Pydantic."""
    with pytest.raises(ValidationError) as excinfo:
        modelo(**datos)
    return [
        {"loc": ("body",) + tuple(e["loc"]), "msg": e["msg"], "type": e["type"]}
        for e in excinfo.value.errors()
    ]


async def _respuesta_del_manejador(errores):
    """Pasa los errores por el manejador global y devuelve el `detail` del cuerpo."""
    respuesta = await main.validation_exception_handler(
        request=None, exc=RequestValidationError(errores)
    )
    return json.loads(respuesta.body)["detail"]


async def _detalle(modelo, **datos):
    return await _respuesta_del_manejador(_errores_de(modelo, **datos))


# ---------------------------------------------------------------------------
# Contrato del cuerpo de error
# ---------------------------------------------------------------------------


async def test_el_422_incluye_los_errores_con_el_campo_por_separado():
    detalle = await _detalle(CourseCreate, name="Álgebra", base_price="")

    assert detalle["code"] == "VALIDATION_ERROR"
    assert detalle["errors"] == [
        {
            "field": "base_price",
            "message": "Input should be a valid number, unable to parse string as a number",
        }
    ]


async def test_cada_error_trae_campo_y_mensaje_sin_mezclarlos():
    """
    El campo no debe venir incrustado dentro del mensaje: si viniera, el
    frontend tendría que partir la cadena para traducirlo, que es justo lo
    frágil que se quiso evitar.
    """
    detalle = await _detalle(CycleCreate)

    assert detalle["errors"], "el 422 debe traer los errores estructurados"
    for error in detalle["errors"]:
        assert error["field"], "todo error de campo debe nombrar su campo"
        assert error["field"] not in error["message"], (
            f"el identificador '{error['field']}' no debe aparecer dentro del "
            f"mensaje: {error['message']!r}"
        )


async def test_un_error_del_modelo_completo_no_inventa_un_campo():
    """
    `end_date > start_date` lo valida un @model_validator, así que el error no
    pertenece a ningún campo concreto. El frontend usa eso para saber que no
    debe anteponer etiqueta alguna.
    """
    detalle = await _detalle(
        CycleCreate,
        name="2026-I",
        start_date="2026-03-01",
        end_date="2026-02-01",
        duration_months=6,
    )

    assert len(detalle["errors"]) == 1
    assert detalle["errors"][0]["field"] == ""
    assert (
        detalle["errors"][0]["message"]
        == "La fecha de fin debe ser posterior a la fecha de inicio"
    )


async def test_se_retira_el_prefijo_de_pydantic_de_los_mensajes_propios():
    detalle = await _detalle(CycleCreate, name="A", start_date="2026-01-01",
                             end_date="2026-06-01", duration_months=0)

    assert detalle["errors"][0]["message"] == "La duración en meses debe ser mayor que 0"
    assert "Value error" not in detalle["message"]


# ---------------------------------------------------------------------------
# Cobertura de los formularios del módulo
# ---------------------------------------------------------------------------

# Todo campo que un formulario de cursos, ciclos, ofertas u horarios pueda
# hacer fallar tiene que llegar identificado, para que el frontend lo pueda
# traducir. La lista de etiquetas vive en frontend/src/services/api.js.
CAMPOS_DE_LOS_FORMULARIOS = {
    "name", "description", "base_price",
    "start_date", "end_date", "duration_months", "status",
    "course_id", "cycle_id", "group_label", "teacher_id",
    "price_override", "capacity",
    "course_offering_id", "day_of_week", "start_time", "end_time", "classroom",
}


@pytest.mark.parametrize(
    "modelo, datos",
    [
        (CycleCreate, {}),
        (CourseCreate, {}),
        (CourseOfferingCreate, {}),
        (ScheduleCreate, {}),
    ],
    ids=["ciclo", "curso", "oferta", "horario"],
)
async def test_los_campos_reportados_son_los_que_el_frontend_sabe_traducir(modelo, datos):
    detalle = await _detalle(modelo, **datos)

    desconocidos = {
        e["field"] for e in detalle["errors"]
        if e["field"] and e["field"] not in CAMPOS_DE_LOS_FORMULARIOS
    }
    assert not desconocidos, (
        f"{sorted(desconocidos)} no tienen etiqueta en ETIQUETAS_CAMPO "
        f"(frontend/src/services/api.js): al usuario le aparecería el nombre "
        f"de la variable en vez del nombre del campo."
    )


async def test_el_mensaje_plano_sigue_disponible_para_clientes_antiguos():
    """`message` y `fields` no cambian: la parte estructurada es aditiva."""
    detalle = await _detalle(CourseCreate, base_price=10)

    assert detalle["message"] == "name: Field required"
    assert detalle["fields"] == ["name: Field required"]
