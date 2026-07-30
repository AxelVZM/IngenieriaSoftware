from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.database import get_db_pool, close_db_pool
from datetime import datetime
import os

# Import routers
from routes import (
    auth,
    students,
    teachers,
    courses,
    cycles,
    schedules,
    enrollments,
    payments,
    packages,
    admin,
    notifications
)

app = FastAPI(title="Academia API", version="2.0.0")

# CORS - Agregar orígenes permitidos
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# Si estás en producción, agregar el dominio del frontend
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)
    # También agregar versión sin trailing slash si la tiene
    if frontend_url.endswith("/"):
        allowed_origins.append(frontend_url[:-1])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Configure Cloudinary
from config.cloudinary import configure_cloudinary
configure_cloudinary()

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(students.router, prefix="/api")
app.include_router(teachers.router, prefix="/api")
app.include_router(courses.router, prefix="/api")
app.include_router(cycles.router, prefix="/api")
app.include_router(schedules.router, prefix="/api")
app.include_router(enrollments.router, prefix="/api")
app.include_router(payments.router, prefix="/api")
app.include_router(packages.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")

@app.on_event("startup")
async def startup():
    await get_db_pool()
    print("✓ Database pool created")

@app.on_event("shutdown")
async def shutdown():
    await close_db_pool()
    print("✓ Database pool closed")

@app.get("/")
async def root():
    return {"message": "Academia API v2.0 - FastAPI", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/test")
async def test_endpoint():
    return {
        "message": "Backend is running",
        "timestamp": datetime.now().isoformat(),
        "status": "ok"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0",
        port=int(os.getenv("PORT", "4000")),
        reload=True
    )