"""
Pruebas de Rendimiento - Módulo de Cursos y Ciclos
Estrategia Pressman, Cap. 20 - Pruebas de rendimiento (carga y esfuerzo)

CONTEXTO MEDIDO (30/07/2026, BD en Railway vía thomas.proxy.rlwy.net):

    ida y vuelta a la BD (SELECT 1) ......  169 / 180 / 398 ms  (min/mediana/máx)
    get_all_courses en caliente ..........  ~620 ms
    ejecución de sus 3 consultas EN el servidor ....  0.23 ms en total
    primera llamada, pool frío ...........  2 825 ms
    crear el pool (min_size=5) ...........  3 526 ms

La base de datos trabaja 0.23 ms de los 620 ms: el 99.96 % restante es red. Por
eso estas pruebas NO miden tiempos de consulta ni uso de índices (a 174 filas en
la tabla más grande, el escaneo secuencial cuesta 0.13 ms y cualquier mejora ahí
es invisible frente a los 180 ms del viaje).

Lo que sí determina el rendimiento es el número de IDAS Y VUELTAS por petición,
y eso es exactamente lo que se afirma aquí. Son pruebas deterministas: cuentan
operaciones, no cronometran, así que no dependen de la red ni de la máquina.

    PRF-01  Presupuesto de idas y vueltas por operación (evita el N+1).
    PRF-03  Esfuerzo: degradación al agotarse el pool de conexiones.

Las pruebas de carga con concurrencia real (PRF-02) y con volumen sembrado
(PRF-04) NO están aquí a propósito: requieren un PostgreSQL local. No deben
correrse contra Railway, que es una base compartida con el equipo.
"""
import asyncio
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import config.database as database
import controllers.courseController as courseController
import controllers.cycleController as cycleController
from models.course import (
    CourseCreate,
    CourseUpdate,
    CourseOfferingUpdate,
)
from models.cycle import CycleCreate, CycleUpdate


# ===========================================================================
# PRF-01 - Presupuesto de idas y vueltas
# ===========================================================================

class ConexionEspia:
    """
    Sustituto de asyncpg.Connection que CUENTA cada operación que cruza la red.

    A diferencia de un AsyncMock, registra el orden y el tipo de cada viaje, que
    es la magnitud que gobierna el tiempo de respuesta de este módulo.
    """

    def __init__(self, respuestas_fetch=None, respuesta_fetchrow=None,
                 respuesta_fetchval=0, respuesta_execute="UPDATE 1"):
        self.viajes = []
        self._respuestas_fetch = list(respuestas_fetch or [])
        self._respuesta_fetchrow = respuesta_fetchrow
        self._respuesta_fetchval = respuesta_fetchval
        # Solo se lee el último token ("UPDATE 1" -> 1), así que el mismo valor
        # sirve para los DELETE.
        self._respuesta_execute = respuesta_execute

    async def fetch(self, query, *args):
        self.viajes.append(("fetch", query))
        return self._respuestas_fetch.pop(0) if self._respuestas_fetch else []

    async def fetchrow(self, query, *args):
        self.viajes.append(("fetchrow", query))
        return self._respuesta_fetchrow

    async def fetchval(self, query, *args):
        self.viajes.append(("fetchval", query))
        return self._respuesta_fetchval

    async def execute(self, query, *args):
        self.viajes.append(("execute", query))
        return self._respuesta_execute

    @property
    def total(self):
        return len(self.viajes)

    def detalle(self):
        """Texto legible para el mensaje de fallo."""
        return "\n".join(
            f"    {i + 1}. {tipo}: {' '.join(q.split())[:70]}"
            for i, (tipo, q) in enumerate(self.viajes)
        )


def datos_sinteticos(n_cursos, ofertas_por_curso=3, horarios_por_oferta=2):
    """
    Genera las 3 respuestas que get_all_courses espera, con el volumen pedido.

    Sirve para comprobar que el número de viajes NO depende del volumen, que es
    la única forma fiable de detectar un N+1: un conteo fijo se puede acertar
    por casualidad, un conteo que no crece no.
    """
    cursos, ofertas, horarios = [], [], []
    id_oferta = id_horario = 0

    for id_curso in range(1, n_cursos + 1):
        cursos.append({
            "id": id_curso,
            "name": f"Curso {id_curso:03d}",
            "base_price": 150.0,
        })
        for grupo in range(ofertas_por_curso):
            id_oferta += 1
            ofertas.append({
                "id": id_oferta,
                "course_id": id_curso,
                "group_label": chr(ord("A") + grupo),
                "cycle_name": "Ciclo 2026-I",
            })
            for _ in range(horarios_por_oferta):
                id_horario += 1
                horarios.append({
                    "id": id_horario,
                    "course_offering_id": id_oferta,
                    "day_of_week": "lunes",
                })

    return [cursos, ofertas, horarios]


# --- El endpoint crítico: /api/courses -------------------------------------
# BG-C6 reemplazó un N+1 (1 + por curso + por oferta) por 3 consultas agrupadas
# en memoria, pero ninguna prueba protegía esa corrección. Estas dos sí.

@pytest.mark.parametrize("n_cursos", [1, 5, 50])
async def test_get_all_courses_hace_3_viajes_sea_cual_sea_el_volumen(n_cursos):
    db = ConexionEspia(datos_sinteticos(n_cursos))

    await courseController.get_all_courses(db)

    assert db.total == 3, (
        f"GET /api/courses debe hacer 3 idas y vueltas y hizo {db.total} "
        f"con {n_cursos} curso(s). A 180 ms por viaje, cada viaje de más son "
        f"180 ms de más en la respuesta.\n{db.detalle()}"
    )


async def test_get_all_courses_no_reintroduce_el_n_mas_1():
    """
    El conteo de viajes debe ser CONSTANTE al crecer el volumen.

    Si alguien vuelve a meter un `await` dentro del bucle `for course in courses`
    (courseController.py:34-37), este conteo empieza a crecer con el número de
    cursos y la prueba cae. Con los 16 cursos actuales serían 16 x 180 ms = 2.9 s
    añadidos al tiempo de respuesta.
    """
    conteos = {}
    for n in (1, 10, 100):
        db = ConexionEspia(datos_sinteticos(n))
        await courseController.get_all_courses(db)
        conteos[n] = db.total

    assert len(set(conteos.values())) == 1, (
        "El número de idas y vueltas crece con el volumen de datos: hay un N+1. "
        f"cursos -> viajes = {conteos}"
    )


async def test_get_all_courses_agrupa_bien_tambien_con_volumen():
    """
    Contrapeso de la prueba anterior: bajar el número de viajes no vale nada si
    se rompe el anidamiento. 20 cursos x 3 ofertas x 2 horarios.
    """
    db = ConexionEspia(datos_sinteticos(20, ofertas_por_curso=3, horarios_por_oferta=2))

    resultado = await courseController.get_all_courses(db)

    assert len(resultado) == 20
    assert all(len(c["offerings"]) == 3 for c in resultado)
    assert all(len(o["schedules"]) == 2 for c in resultado for o in c["offerings"])


# --- Presupuesto del resto de las operaciones del módulo -------------------

CICLO_NUEVO = CycleCreate(
    name="Ciclo 2026-II",
    start_date="2026-08-01",
    end_date="2026-12-15",
    duration_months=5,
)
CURSO_NUEVO = CourseCreate(name="Álgebra", description="Curso base", base_price=150.0)


@pytest.mark.parametrize("etiqueta, operacion, presupuesto", [
    # Lecturas: un solo viaje cada una.
    ("GET  /api/cycles",                    lambda db: cycleController.get_all_cycles(db), 1),
    ("GET  /api/cycles/{id}",               lambda db: cycleController.get_cycle_by_id(1, db), 1),
    ("GET  /api/cycles/active",             lambda db: cycleController.get_active_cycle(db), 1),
    ("GET  /api/courses/offerings/{ciclo}",  lambda db: courseController.get_course_offerings(1, db), 1),
    # Escrituras: un solo viaje.
    ("POST /api/cycles",                    lambda db: cycleController.create_cycle(CICLO_NUEVO, db), 1),
    ("POST /api/courses",                   lambda db: courseController.create_course(CURSO_NUEVO, db), 1),
    ("PUT  /api/cycles/{id}",               lambda db: cycleController.update_cycle(1, CycleUpdate(status="closed"), db), 1),
    ("PUT  /api/courses/{id}",              lambda db: courseController.update_course(1, CourseUpdate(base_price=200.0), db), 1),
    ("PUT  /api/courses/offerings/{id}",    lambda db: courseController.update_course_offering(1, CourseOfferingUpdate(capacity=40), db), 1),
    # Los borrados hacen 2: la comprobación de integridad de BG-C4 y el DELETE.
    ("DEL  /api/cycles/{id}",               lambda db: cycleController.delete_cycle(1, db), 2),
    ("DEL  /api/courses/{id}",              lambda db: courseController.delete_course(1, db), 2),
    ("DEL  /api/courses/offerings/{id}",    lambda db: courseController.delete_course_offering(1, db), 2),
])
async def test_presupuesto_de_viajes_por_operacion(etiqueta, operacion, presupuesto):
    """
    Fija el costo en idas y vueltas de cada operación del módulo.

    Que caiga no significa "está mal": significa que alguien cambió el costo de
    una operación y debe decidir a conciencia si vale esos ~180 ms.
    """
    db = ConexionEspia(respuesta_fetchrow={"id": 1})

    await operacion(db)

    assert db.total == presupuesto, (
        f"{etiqueta} tenía un presupuesto de {presupuesto} ida(s) y vuelta(s) "
        f"y hizo {db.total}.\n{db.detalle()}"
    )


# ===========================================================================
# PRF-03 - Esfuerzo: agotamiento del pool de conexiones
# ===========================================================================
#
# El pool se crea con max_size=20 y cada GET /api/courses retiene su conexión
# ~620 ms, así que el techo de ese endpoint es ~32 peticiones/s, impuesto por la
# espera de red y no por la CPU ni por la base.
#
# Pressman no pregunta si el sistema aguanta la sobrecarga, sino si DEGRADA DE
# FORMA CONTROLADA. Aquí se reproduce la saturación a escala reducida
# (CAPACIDAD conexiones en vez de 20, DURACION en vez de 620 ms) para observar
# qué le pasa a la petición número 21.

CAPACIDAD = 4        # representa max_size=20
DURACION = 0.05      # representa los ~620 ms que dura una petición


class PoolSaturable:
    """Pool con un número fijo de conexiones, como asyncpg.create_pool(max_size=N)."""

    def __init__(self, max_size):
        self.max_size = max_size
        self._libres = asyncio.Semaphore(max_size)
        self.en_uso = 0
        self.pico_en_uso = 0

    def acquire(self, *, timeout=None):
        return _Adquisicion(self, timeout)


class _Adquisicion:
    """Lo que devuelve pool.acquire(): un gestor de contexto asíncrono.

    Replica el `timeout` de asyncpg.Pool.acquire(): si no hay conexión libre
    antes de que venza, levanta asyncio.TimeoutError sin tomar ninguna.
    """

    def __init__(self, pool, timeout=None):
        self._pool = pool
        self._timeout = timeout

    async def __aenter__(self):
        if self._timeout is not None:
            await asyncio.wait_for(self._pool._libres.acquire(), timeout=self._timeout)
        else:
            await self._pool._libres.acquire()
        self._pool.en_uso += 1
        self._pool.pico_en_uso = max(self._pool.pico_en_uso, self._pool.en_uso)
        return ConexionEspia()

    async def __aexit__(self, *exc):
        self._pool.en_uso -= 1
        self._pool._libres.release()
        return False


@pytest.fixture
def instalar_pool(monkeypatch):
    """Reemplaza el pool real por uno saturable, sin tocar la red.

    También reduce ACQUIRE_TIMEOUT_SECONDS a la escala de estas pruebas
    (DURACION en vez de los ~620 ms reales): de lo contrario el timeout de
    producción (10 s) nunca se alcanzaría con DURACION=0.05s y las pruebas de
    sobrecarga tardarían minutos en lugar de fallar rápido.
    """

    def _instalar(max_size=CAPACIDAD):
        pool = PoolSaturable(max_size)

        async def _get_db_pool():
            return pool

        monkeypatch.setattr(database, "get_db_pool", _get_db_pool)
        monkeypatch.setattr(database, "ACQUIRE_TIMEOUT_SECONDS", DURACION * 1.5)
        return pool

    return _instalar


async def _peticion(duracion=DURACION):
    """
    Simula una petición: pide conexión por la vía real (config.database.get_db),
    la retiene mientras "consulta" y la libera. Devuelve lo que esperó por ella
    (incluido el caso en que el pool.acquire() vence su timeout: esa espera
    también es la que sentiría el cliente antes de recibir un 503).
    """
    inicio = time.perf_counter()
    generador = database.get_db()
    try:
        await generador.__anext__()      # aquí se espera si el pool está lleno
    except asyncio.TimeoutError:
        return time.perf_counter() - inicio
    espera = time.perf_counter() - inicio

    await asyncio.sleep(duracion)
    await generador.aclose()
    return espera


async def test_dentro_de_la_capacidad_no_hay_encolamiento(instalar_pool):
    """Con tantas peticiones como conexiones, ninguna debe esperar."""
    pool = instalar_pool()

    esperas = await asyncio.gather(*[_peticion() for _ in range(CAPACIDAD)])

    assert pool.pico_en_uso == CAPACIDAD
    assert max(esperas) < DURACION / 2, (
        f"Hubo encolamiento sin llegar al límite del pool: espera máxima "
        f"{max(esperas) * 1000:.0f} ms"
    )


async def test_el_pool_nunca_entrega_mas_conexiones_que_su_maximo(instalar_pool):
    """Invariante del pool: es el que convierte la sobrecarga en espera."""
    pool = instalar_pool()

    await asyncio.gather(*[_peticion(DURACION / 2) for _ in range(CAPACIDAD * 5)])

    assert pool.pico_en_uso <= CAPACIDAD
    assert pool.en_uso == 0, "Quedaron conexiones sin devolver al pool"


async def test_la_espera_por_una_conexion_crece_con_la_sobrecarga(instalar_pool):
    """
    Documenta CÓMO degrada: la espera crece de forma proporcional a la
    sobrecarga, sin ningún techo. Es la evidencia del defecto que registra la
    prueba siguiente.
    """
    esperas_maximas = {}
    for factor in (1, 2, 4):
        instalar_pool()
        esperas = await asyncio.gather(
            *[_peticion() for _ in range(CAPACIDAD * factor)]
        )
        esperas_maximas[factor] = max(esperas)

    assert esperas_maximas[4] > esperas_maximas[1], (
        f"espera máxima por factor de sobrecarga = {esperas_maximas}"
    )


async def test_la_sobrecarga_sostenida_no_debe_encolar_sin_limite(instalar_pool):
    """
    Prueba de esfuerzo: 6 veces la capacidad del pool a la vez.

    DEF-07 (corregido): `pool.acquire()` en config/database.py ahora recibe
    `timeout=ACQUIRE_TIMEOUT_SECONDS`, así que bajo sobrecarga sostenida la
    espera por una conexión libre está acotada — quien no consigue conexión a
    tiempo falla rápido (503, DB_UNAVAILABLE) en vez de quedar colgado sin
    respuesta.
    """
    instalar_pool()
    limite_aceptable = DURACION * 2

    esperas = await asyncio.gather(*[_peticion() for _ in range(CAPACIDAD * 6)])

    assert max(esperas) <= limite_aceptable, (
        f"Alguna petición esperó {max(esperas) * 1000:.0f} ms por una conexión, "
        f"por encima del límite de {limite_aceptable * 1000:.0f} ms. "
        f"Escalado a producción (max_size=20, ~620 ms por petición) son "
        f"~{max(esperas) / DURACION * 0.62:.1f} s de espera."
    )
