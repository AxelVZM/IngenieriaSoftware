from fastapi import APIRouter, Depends, HTTPException, status
from models.course import ScheduleCreate, ScheduleUpdate
from middleware.auth import require_role
from config.database import get_db
import asyncpg
import controllers.scheduleController as scheduleController

router = APIRouter(prefix="/schedules", tags=["schedules"])

@router.post("", dependencies=[Depends(require_role(["admin"]))], status_code=status.HTTP_201_CREATED)
async def create_schedule(schedule: ScheduleCreate, db: asyncpg.Connection = Depends(get_db)):
    if not schedule.course_offering_id:
        raise HTTPException(status_code=400, detail="course_offering_id es requerido")
    return await scheduleController.create_schedule(schedule, db)

# Support both naming conventions
@router.get("/course-offering/{course_offering_id}")
async def get_schedules_by_offering(course_offering_id: int, db: asyncpg.Connection = Depends(get_db)):
    return await scheduleController.get_schedules_by_offering(course_offering_id, db)

@router.get("/offering/{course_offering_id}")
async def get_schedules_by_offering_alt(course_offering_id: int, db: asyncpg.Connection = Depends(get_db)):
    """Alternative endpoint for compatibility"""
    return await scheduleController.get_schedules_by_offering(course_offering_id, db)

@router.get("/package-offering/{package_offering_id}")
async def get_schedules_by_package(package_offering_id: int, db: asyncpg.Connection = Depends(get_db)):
    return await scheduleController.get_schedules_by_package(package_offering_id, db)

@router.put("/{schedule_id}", dependencies=[Depends(require_role(["admin"]))])
async def update_schedule(schedule_id: int, schedule: ScheduleUpdate, db: asyncpg.Connection = Depends(get_db)):
    return await scheduleController.update_schedule(schedule_id, schedule, db)

@router.delete("/{schedule_id}", dependencies=[Depends(require_role(["admin"]))])
async def delete_schedule(schedule_id: int, db: asyncpg.Connection = Depends(get_db)):
    return await scheduleController.delete_schedule(schedule_id, db)

@router.get("")
async def get_all_schedules(db: asyncpg.Connection = Depends(get_db)):
    return await scheduleController.get_all_schedules(db)
