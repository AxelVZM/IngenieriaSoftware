import asyncpg
from models.course import CourseCreate, CourseUpdate, CourseOfferingCreate, CourseOfferingUpdate

async def get_all_courses(db: asyncpg.Connection):
    courses = await db.fetch("SELECT * FROM courses ORDER BY name")
    courses_list = []
    
    for course in courses:
        course_dict = dict(course)
        
        # Get offerings for this course
        offerings = await db.fetch(
            """SELECT co.*, cyc.name as cycle_name, 
                      t.first_name, t.last_name
               FROM course_offerings co
               LEFT JOIN cycles cyc ON co.cycle_id = cyc.id
               LEFT JOIN teachers t ON co.teacher_id = t.id
               WHERE co.course_id = $1
               ORDER BY cyc.start_date DESC, co.group_label""",
            course['id']
        )
        
        offerings_list = []
        for offering in offerings:
            offering_dict = dict(offering)
            
            # Get schedules for this offering (like Node.js)
            schedules = await db.fetch(
                "SELECT * FROM schedules WHERE course_offering_id = $1",
                offering['id']
            )
            offering_dict['schedules'] = [dict(s) for s in schedules]
            offerings_list.append(offering_dict)
        
        course_dict['offerings'] = offerings_list
        courses_list.append(course_dict)
    
    return courses_list

async def create_course(data: CourseCreate, db: asyncpg.Connection):
    result = await db.fetchrow(
        """INSERT INTO courses (name, description, base_price)
           VALUES ($1, $2, $3) RETURNING id""",
        data.name, data.description, data.base_price
    )
    return {"id": result['id'], "message": "Curso creado exitosamente"}

async def update_course(course_id: int, data: CourseUpdate, db: asyncpg.Connection):
    fields = []
    values = []
    idx = 1
    
    for field, value in data.dict(exclude_unset=True).items():
        fields.append(f"{field} = ${idx}")
        values.append(value)
        idx += 1
    
    if not fields:
        return {"message": "No hay campos para actualizar"}
    
    values.append(course_id)
    query = f"UPDATE courses SET {', '.join(fields)} WHERE id = ${idx}"
    await db.execute(query, *values)
    return {"message": "Curso actualizado correctamente"}

async def delete_course(course_id: int, db: asyncpg.Connection):
    await db.execute("DELETE FROM courses WHERE id = $1", course_id)
    return {"message": "Curso eliminado correctamente"}

async def get_course_offerings(cycle_id: int, db: asyncpg.Connection):
    offerings = await db.fetch(
        """SELECT co.*, c.name as course_name, c.description, c.base_price,
                  t.first_name as teacher_first_name, t.last_name as teacher_last_name,
                  cyc.name as cycle_name
           FROM course_offerings co
           JOIN courses c ON co.course_id = c.id
           LEFT JOIN teachers t ON co.teacher_id = t.id
           JOIN cycles cyc ON co.cycle_id = cyc.id
           WHERE co.cycle_id = $1
           ORDER BY c.name, co.group_label""",
        cycle_id
    )
    return [dict(o) for o in offerings]

async def create_course_offering(data: CourseOfferingCreate, db: asyncpg.Connection):
    result = await db.fetchrow(
        """INSERT INTO course_offerings (course_id, cycle_id, group_label, teacher_id, price_override, capacity)
           VALUES ($1, $2, $3, $4, $5, $6) RETURNING id""",
        data.course_id, data.cycle_id, data.group_label, data.teacher_id, data.price_override, data.capacity
    )
    return {"id": result['id'], "message": "Oferta de curso creada exitosamente"}

async def update_course_offering(offering_id: int, data: CourseOfferingUpdate, db: asyncpg.Connection):
    fields = []
    values = []
    idx = 1
    
    for field, value in data.dict(exclude_unset=True).items():
        fields.append(f"{field} = ${idx}")
        values.append(value)
        idx += 1
    
    if not fields:
        return {"message": "No hay campos para actualizar"}
    
    values.append(offering_id)
    query = f"UPDATE course_offerings SET {', '.join(fields)} WHERE id = ${idx}"
    await db.execute(query, *values)
    return {"message": "Oferta actualizada correctamente"}

async def delete_course_offering(offering_id: int, db: asyncpg.Connection):
    await db.execute("DELETE FROM course_offerings WHERE id = $1", offering_id)
    return {"message": "Oferta eliminada correctamente"}
