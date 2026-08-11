"""
Pruebas de Unidad (Caja Blanca) - Controlador de Ciclos
Estrategia Pressman, Cap. 17 - Sección 2.1

La conexión a la base de datos (asyncpg) se reemplaza por un mock (AsyncMock),
de modo que se verifica la LÓGICA del controlador sin depender de PostgreSQL.
"""
import sys
from pathlib import Path
from datetime import date
from unittest.mock import AsyncMock

import pytest

# Permitir importar los paquetes del backend (controllers, models, ...)
sys.path.insert(0, str(Path(__file__).parent.parent))

import controllers.cycleController as cycleController
from models.cycle import CycleCreate, CycleUpdate


# ---------------------------------------------------------------------------
# create_cycle
# ---------------------------------------------------------------------------
async def test_create_cycle_devuelve_id_y_mensaje():
    db = AsyncMock()
    db.fetchrow.return_value = {"id": 1}

    data = CycleCreate(
        name="Ciclo 2026-I",
        start_date=date(2026, 3, 1),
        end_date=date(2026, 7, 31),
        duration_months=5,
        status="open",
    )

    result = await cycleController.create_cycle(data, db)

    assert result["id"] == 1
    assert result["message"] == "Ciclo creado exitosamente"
    db.fetchrow.assert_awaited_once()


# ---------------------------------------------------------------------------
# get_active_cycle
# ---------------------------------------------------------------------------
async def test_get_active_cycle_retorna_ciclo_abierto():
    db = AsyncMock()
    db.fetchrow.return_value = {"id": 3, "name": "Ciclo 2026-I", "status": "open"}

    result = await cycleController.get_active_cycle(db)

    assert result is not None
    assert result["status"] == "open"


async def test_get_active_cycle_sin_ciclo_retorna_none():
    db = AsyncMock()
    db.fetchrow.return_value = None

    result = await cycleController.get_active_cycle(db)

    assert result is None


# ---------------------------------------------------------------------------
# get_cycle_by_id
# ---------------------------------------------------------------------------
async def test_get_cycle_by_id_inexistente_retorna_none():
    db = AsyncMock()
    db.fetchrow.return_value = None

    result = await cycleController.get_cycle_by_id(99999, db)

    assert result is None


# ---------------------------------------------------------------------------
# get_all_cycles
# ---------------------------------------------------------------------------
async def test_get_all_cycles_retorna_lista_de_dicts():
    db = AsyncMock()
    db.fetch.return_value = [
        {"id": 1, "name": "Ciclo 2026-I"},
        {"id": 2, "name": "Ciclo 2025-II"},
    ]

    result = await cycleController.get_all_cycles(db)

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["name"] == "Ciclo 2026-I"


# ---------------------------------------------------------------------------
# update_cycle
# ---------------------------------------------------------------------------
async def test_update_cycle_sin_campos_no_ejecuta_query():
    db = AsyncMock()

    data = CycleUpdate()  # ningún campo seteado

    result = await cycleController.update_cycle(1, data, db)

    assert result["message"] == "No hay campos para actualizar"
    db.execute.assert_not_awaited()


async def test_update_cycle_con_campos_ejecuta_update():
    db = AsyncMock()
    db.execute.return_value = "UPDATE 1"  # se actualizó 1 fila

    data = CycleUpdate(status="closed")

    result = await cycleController.update_cycle(1, data, db)

    assert result["message"] == "Ciclo actualizado correctamente"
    db.execute.assert_awaited_once()
    # El id del ciclo debe ir como último parámetro de la query
    args = db.execute.await_args.args
    assert args[-1] == 1
    assert "UPDATE cycles SET" in args[0]


# ---------------------------------------------------------------------------
# delete_cycle
# ---------------------------------------------------------------------------
async def test_delete_cycle_ejecuta_delete_con_id():
    db = AsyncMock()
    db.fetchval.return_value = 0          # sin ofertas asociadas (BG-C4)
    db.execute.return_value = "DELETE 1"  # se borró 1 fila (BG-C2)

    result = await cycleController.delete_cycle(7, db)

    assert result["message"] == "Ciclo eliminado correctamente"
    db.execute.assert_awaited_once()
    args = db.execute.await_args.args
    assert "DELETE FROM cycles" in args[0]
    assert args[1] == 7
