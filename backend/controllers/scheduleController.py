import asyncpg
from models.course import ScheduleCreate, ScheduleUpdate
from datetime import time as py_time

async def create_schedule(data: ScheduleCreate, db: asyncpg.Connection):
    # Parse time strings to time objects
    st = data.start_time
    et = data.end_time
    
    if hasattr(st, 'strftime'):
        st = st.strftime("%H:%M:%S")
    else:
        st = str(st)
        # Add seconds if not present (HH:MM -> HH:MM:00)
        if st.count(':') == 1:
            st = st + ":00"
        
    if hasattr(et, 'strftime'):
        et = et.strftime("%H:%M:%S")
    else:
        et = str(et)
        # Add seconds if not present (HH:MM -> HH:MM:00)
        if et.count(':') == 1:
            et = et + ":00"
    
    # Convert to time objects for asyncpg
    h, m, s = map(int, st.split(':'))
    t_start = py_time(h, m, s)
    
    h, m, s = map(int, et.split(':'))
    t_end = py_time(h, m, s)
    
    result = await db.fetchrow(
        """INSERT INTO schedules (course_offering_id, day_of_week, start_time, end_time, classroom)
           VALUES ($1, $2::day_of_week, $3, $4, $5) RETURNING id""",
        data.course_offering_id, data.day_of_week, t_start, t_end, data.classroom
    )
    return {"id": result['id'], "message": "Horario creado exitosamente"}

async def get_schedules_by_offering(offering_id: int, db: asyncpg.Connection):
    schedules = await db.fetch(
        """SELECT s.*, co.id as course_offering_id, co.course_id, co.group_label,
                  c.name as course_name, cyc.name as cycle_name
           FROM schedules s
           LEFT JOIN course_offerings co ON s.course_offering_id = co.id
           LEFT JOIN courses c ON co.course_id = c.id
           LEFT JOIN cycles cyc ON co.cycle_id = cyc.id
           WHERE s.course_offering_id = $1
           ORDER BY s.day_of_week, s.start_time""",
        offering_id
    )
    return [dict(s) for s in schedules]

async def get_schedules_by_package(package_id: int, db: asyncpg.Connection):
    # Try exact mapping first
    mapped = await db.fetch(
        """SELECT s.*, co.id AS course_offering_id, co.course_id, co.group_label,
                  c.name AS course_name, cyc.name AS cycle_name,
                  t.first_name AS teacher_first_name, t.last_name AS teacher_last_name
           FROM package_offering_courses poc
           JOIN course_offerings co ON co.id = poc.course_offering_id
           JOIN courses c ON c.id = co.course_id
           LEFT JOIN teachers t ON t.id = co.teacher_id
           JOIN cycles cyc ON cyc.id = co.cycle_id
           LEFT JOIN schedules s ON s.course_offering_id = co.id
           WHERE poc.package_offering_id = $1
           ORDER BY c.id, co.id, s.day_of_week, s.start_time""",
        package_id
    )
    
    if mapped:
        return [dict(s) for s in mapped]
    
    # Fallback
    rows = await db.fetch(
        """SELECT s.*, co.id as course_offering_id, co.course_id, co.group_label,
                  c.name as course_name, cyc.name as cycle_name,
                  t.first_name AS teacher_first_name, t.last_name AS teacher_last_name
           FROM package_offerings po
           JOIN packages p ON po.package_id = p.id
           JOIN package_courses pc ON pc.package_id = p.id
           JOIN course_offerings co ON co.course_id = pc.course_id AND co.cycle_id = po.cycle_id
           JOIN courses c ON c.id = co.course_id
           LEFT JOIN teachers t ON t.id = co.teacher_id
           JOIN cycles cyc ON cyc.id = co.cycle_id
           LEFT JOIN schedules s ON s.course_offering_id = co.id
           WHERE po.id = $1
           ORDER BY c.id, co.id, s.day_of_week, s.start_time""",
        package_id
    )
    return [dict(s) for s in rows]

async def update_schedule(schedule_id: int, data: ScheduleUpdate, db: asyncpg.Connection):
    fields = []
    values = []
    idx = 1
    
    for field, value in data.dict(exclude_unset=True).items():
        fields.append(f"{field} = ${idx}")
        values.append(value)
        idx += 1
    
    if not fields:
        return {"message": "No hay campos para actualizar"}
    
    values.append(schedule_id)
    query = f"UPDATE schedules SET {', '.join(fields)} WHERE id = ${idx}"
    await db.execute(query, *values)
    return {"message": "Horario actualizado correctamente"}

async def delete_schedule(schedule_id: int, db: asyncpg.Connection):
    await db.execute("DELETE FROM schedules WHERE id = $1", schedule_id)
    return {"message": "Horario eliminado correctamente"}

async def get_all_schedules(db: asyncpg.Connection):
    schedules = await db.fetch(
        """SELECT s.*, co.id as course_offering_id, co.course_id, co.group_label,
                  c.name as course_name, cyc.name as cycle_name
           FROM schedules s
           LEFT JOIN course_offerings co ON s.course_offering_id = co.id
           LEFT JOIN courses c ON co.course_id = c.id
           LEFT JOIN cycles cyc ON co.cycle_id = cyc.id
           ORDER BY co.course_id, s.day_of_week, s.start_time"""
    )
    return [dict(s) for s in schedules]
