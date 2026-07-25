from fastapi import APIRouter, Depends, HTTPException, status
from models.cycle import CycleCreate, CycleUpdate
from middleware.auth import require_role
from config.database import get_db
import asyncpg
import controllers.cycleController as cycleController

router = APIRouter(prefix="/cycles", tags=["cycles"])

@router.get("")
async def get_cycles(db: asyncpg.Connection = Depends(get_db)):
    return await cycleController.get_all_cycles(db)

@router.get("/active")
async def get_active_cycle(db: asyncpg.Connection = Depends(get_db)):
    cycle = await cycleController.get_active_cycle(db)
    if not cycle:
        raise HTTPException(status_code=404, detail="No hay ciclo activo")
    return cycle

@router.get("/{cycle_id}")
async def get_cycle(cycle_id: int, db: asyncpg.Connection = Depends(get_db)):
    cycle = await cycleController.get_cycle_by_id(cycle_id, db)
    if not cycle:
        raise HTTPException(status_code=404, detail="Ciclo no encontrado")
    return cycle

@router.post("", dependencies=[Depends(require_role(["admin"]))], status_code=status.HTTP_201_CREATED)
async def create_cycle(cycle: CycleCreate, db: asyncpg.Connection = Depends(get_db)):
    return await cycleController.create_cycle(cycle, db)

@router.put("/{cycle_id}", dependencies=[Depends(require_role(["admin"]))])
async def update_cycle(cycle_id: int, cycle: CycleUpdate, db: asyncpg.Connection = Depends(get_db)):
    return await cycleController.update_cycle(cycle_id, cycle, db)

@router.delete("/{cycle_id}", dependencies=[Depends(require_role(["admin"]))])
async def delete_cycle(cycle_id: int, db: asyncpg.Connection = Depends(get_db)):
    return await cycleController.delete_cycle(cycle_id, db)
