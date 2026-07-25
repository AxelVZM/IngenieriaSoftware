from fastapi import APIRouter, Depends, HTTPException, status
from models.enrollment import PackageCreate, PackageUpdate, PackageOfferingCreate
from middleware.auth import require_role
from config.database import get_db
import asyncpg
import controllers.packageController as packageController

router = APIRouter(prefix="/packages", tags=["packages"])

@router.get("")
async def get_packages(db: asyncpg.Connection = Depends(get_db)):
    return await packageController.get_all_packages(db)

@router.post("", dependencies=[Depends(require_role(["admin"]))], status_code=status.HTTP_201_CREATED)
async def create_package(package: PackageCreate, db: asyncpg.Connection = Depends(get_db)):
    return await packageController.create_package(package, db)

@router.put("/{package_id}", dependencies=[Depends(require_role(["admin"]))])
async def update_package(package_id: int, package: PackageUpdate, db: asyncpg.Connection = Depends(get_db)):
    return await packageController.update_package(package_id, package, db)

@router.delete("/{package_id}", dependencies=[Depends(require_role(["admin"]))])
async def delete_package(package_id: int, db: asyncpg.Connection = Depends(get_db)):
    return await packageController.delete_package(package_id, db)

# Package courses management
@router.post("/{package_id}/courses", dependencies=[Depends(require_role(["admin"]))])
async def add_course(package_id: int, data: dict, db: asyncpg.Connection = Depends(get_db)):
    course_id = data.get("course_id")
    if not course_id:
        raise HTTPException(status_code=400, detail="course_id es requerido")
    return await packageController.add_course_to_package(package_id, course_id, db)

@router.delete("/{package_id}/courses/{course_id}", dependencies=[Depends(require_role(["admin"]))])
async def remove_course(package_id: int, course_id: int, db: asyncpg.Connection = Depends(get_db)):
    return await packageController.remove_course_from_package(package_id, course_id, db)

# Package offerings
@router.get("/offerings")
async def get_offerings(cycle_id: int = None, db: asyncpg.Connection = Depends(get_db)):
    if cycle_id:
        return await packageController.get_package_offerings(cycle_id, db)
    return await packageController.get_all_package_offerings(db)

@router.get("/offerings/{cycle_id}")
async def get_offerings_by_cycle(cycle_id: int, db: asyncpg.Connection = Depends(get_db)):
    return await packageController.get_package_offerings(cycle_id, db)

@router.post("/offerings", dependencies=[Depends(require_role(["admin"]))], status_code=status.HTTP_201_CREATED)
async def create_offering(offering: PackageOfferingCreate, db: asyncpg.Connection = Depends(get_db)):
    return await packageController.create_package_offering(offering, db)

# Package offering courses management
@router.post("/offerings/{package_offering_id}/courses", dependencies=[Depends(require_role(["admin"]))])
async def add_offering_course(package_offering_id: int, data: dict, db: asyncpg.Connection = Depends(get_db)):
    course_offering_id = data.get("course_offering_id")
    if not course_offering_id:
        raise HTTPException(status_code=400, detail="course_offering_id es requerido")
    return await packageController.add_offering_course(package_offering_id, course_offering_id, db)

@router.delete("/offerings/{package_offering_id}/courses/{course_offering_id}", dependencies=[Depends(require_role(["admin"]))])
async def remove_offering_course(package_offering_id: int, course_offering_id: int, db: asyncpg.Connection = Depends(get_db)):
    return await packageController.remove_offering_course(package_offering_id, course_offering_id, db)

@router.get("/offerings/{package_offering_id}/courses")
async def get_offering_courses(package_offering_id: int, db: asyncpg.Connection = Depends(get_db)):
    return await packageController.get_offering_courses(package_offering_id, db)
