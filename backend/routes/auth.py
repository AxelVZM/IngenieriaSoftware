from fastapi import APIRouter, Depends, HTTPException, status
from models.student import StudentCreate
from models.user import UserLogin
from config.database import get_db
import asyncpg
import controllers.authController as authController

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: StudentCreate, db: asyncpg.Connection = Depends(get_db)):
    result = await authController.register_student(user, db)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/login")
async def login(credentials: UserLogin, db: asyncpg.Connection = Depends(get_db)):
    result = await authController.login_user(credentials, db)
    if "error" in result:
        raise HTTPException(status_code=401, detail=result["error"])
    return result
