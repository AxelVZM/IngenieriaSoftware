from fastapi import APIRouter, Depends, HTTPException, status
from models.course import CourseCreate, CourseUpdate, CourseOfferingCreate, CourseOfferingUpdate
from middleware.auth import require_role
from config.database import get_db
import asyncpg
import controllers.courseController as courseController

router = APIRouter(prefix="/courses", tags=["courses"])

@router.get("")
async def get_courses(db: asyncpg.Connection = Depends(get_db)):
    return await courseController.get_all_courses(db)

@router.post("", dependencies=[Depends(require_role(["admin"]))], status_code=status.HTTP_201_CREATED)
async def create_course(course: CourseCreate, db: asyncpg.Connection = Depends(get_db)):
    return await courseController.create_course(course, db)

@router.put("/{course_id}", dependencies=[Depends(require_role(["admin"]))])
async def update_course(course_id: int, course: CourseUpdate, db: asyncpg.Connection = Depends(get_db)):
    return await courseController.update_course(course_id, course, db)

@router.delete("/{course_id}", dependencies=[Depends(require_role(["admin"]))])
async def delete_course(course_id: int, db: asyncpg.Connection = Depends(get_db)):
    return await courseController.delete_course(course_id, db)

@router.get("/offerings/{cycle_id}")
async def get_offerings(cycle_id: int, db: asyncpg.Connection = Depends(get_db)):
    return await courseController.get_course_offerings(cycle_id, db)

@router.post("/offerings", dependencies=[Depends(require_role(["admin"]))], status_code=status.HTTP_201_CREATED)
async def create_offering(offering: CourseOfferingCreate, db: asyncpg.Connection = Depends(get_db)):
    return await courseController.create_course_offering(offering, db)

@router.put("/offerings/{offering_id}", dependencies=[Depends(require_role(["admin"]))])
async def update_offering(offering_id: int, offering: CourseOfferingUpdate, db: asyncpg.Connection = Depends(get_db)):
    return await courseController.update_course_offering(offering_id, offering, db)

@router.delete("/offerings/{offering_id}", dependencies=[Depends(require_role(["admin"]))])
async def delete_offering(offering_id: int, db: asyncpg.Connection = Depends(get_db)):
    return await courseController.delete_course_offering(offering_id, db)
