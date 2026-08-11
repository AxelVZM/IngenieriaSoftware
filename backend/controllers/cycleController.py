import asyncpg
from fastapi import HTTPException
from models.cycle import CycleCreate, CycleUpdate

async def get_all_cycles(db: asyncpg.Connection):
    cycles = await db.fetch("SELECT * FROM cycles ORDER BY start_date DESC")
    return [dict(c) for c in cycles]

async def get_cycle_by_id(cycle_id: int, db: asyncpg.Connection):
    cycle = await db.fetchrow("SELECT * FROM cycles WHERE id = $1", cycle_id)
    if not cycle:
        return None
    return dict(cycle)

async def create_cycle(data: CycleCreate, db: asyncpg.Connection):
    result = await db.fetchrow(
        """INSERT INTO cycles (name, start_date, end_date, duration_months, status)
           VALUES ($1, $2, $3, $4, $5) RETURNING id""",
        data.name, data.start_date, data.end_date, data.duration_months, data.status
    )
    return {"id": result['id'], "message": "Ciclo creado exitosamente"}

async def update_cycle(cycle_id: int, data: CycleUpdate, db: asyncpg.Connection):
    fields = []
    values = []
    idx = 1
    
    for field, value in data.model_dump(exclude_unset=True).items():
        fields.append(f"{field} = ${idx}")
        values.append(value)
        idx += 1

    if not fields:
        return {"message": "No hay campos para actualizar"}

    values.append(cycle_id)
    query = f"UPDATE cycles SET {', '.join(fields)} WHERE id = ${idx}"
    result = await db.execute(query, *values)

    # Verificar que el ciclo realmente existía: sin esto se respondía
    # "actualizado correctamente" para cualquier id inexistente.
    if int(result.split()[-1]) == 0:
        raise HTTPException(status_code=404, detail="Ciclo no encontrado")

    return {"message": "Ciclo actualizado correctamente"}

async def delete_cycle(cycle_id: int, db: asyncpg.Connection):
    # BG-C4: no permitir borrar un ciclo con ofertas asociadas
    offerings = await db.fetchval(
        "SELECT COUNT(*) FROM course_offerings WHERE cycle_id = $1", cycle_id
    )
    if offerings and offerings > 0:
        raise HTTPException(
            status_code=409,
            detail=f"No se puede eliminar: el ciclo tiene {offerings} oferta(s) asociada(s)"
        )

    # BG-C2: verificar que el ciclo realmente existía
    result = await db.execute("DELETE FROM cycles WHERE id = $1", cycle_id)
    if int(result.split()[-1]) == 0:
        raise HTTPException(status_code=404, detail="Ciclo no encontrado")

    return {"message": "Ciclo eliminado correctamente"}

async def get_active_cycle(db: asyncpg.Connection):
    """Get the currently active cycle (status='open')"""
    cycle = await db.fetchrow(
        "SELECT * FROM cycles WHERE status = 'open' ORDER BY start_date DESC LIMIT 1"
    )
    if not cycle:
        return None
    return dict(cycle)
