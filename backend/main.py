"""
Punto de entrada de la API.

Cambios respecto a la version revisada:
  - Manejadores globales de excepciones: ninguna excepcion no controlada
    llega al cliente como stacktrace.
  - Formato de error unificado para HTTPException, errores de validacion
    (422), errores de base de datos y errores 500.
  - Se reemplaza @app.on_event (deprecado) por el gestor `lifespan`.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

import asyncpg
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.cloudinary import configure_cloudinary
from config.database import close_db_pool, get_db_pool
from utils.errors import DB_UNAVAILABLE_MESSAGE, GENERIC_SERVER_MESSAGE

# Importar routers
from routes import (
    admin,
    auth,
    courses,
    cycles,
    enrollments,
    notifications,
    packages,
    payments,
    schedules,
    students,
    teachers,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("academia")


# ---------------------------------------------------------------------------
# Ciclo de vida
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_db_pool()
    configure_cloudinary()
    logger.info("Pool de base de datos creado y Cloudinary configurado")
    yield
    await close_db_pool()
    logger.info("Pool de base de datos cerrado")


app = FastAPI(title="Academia API", version="2.1.0", lifespan=lifespan)


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    frontend_url = frontend_url.strip()
    allowed_origins.append(frontend_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys(allowed_origins)),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Manejadores globales de excepciones
# ---------------------------------------------------------------------------


def _error_body(code: str, message: str) -> dict:
    return {"detail": {"code": code, "message": message}}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Normaliza todas las HTTPException al formato {"detail": {code, message}}.

    Acepta tanto las que ya vienen con el formato nuevo (dict) como las
    antiguas que pasaban un string.
    """
    detail = exc.detail
    if isinstance(detail, dict) and "message" in detail:
        body = {"detail": detail}
    else:
        body = _error_body("HTTP_ERROR", str(detail))

    return JSONResponse(
        status_code=exc.status_code, content=body, headers=exc.headers
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Convierte los errores 422 de Pydantic en un mensaje legible.

    Además del texto ya armado se envía `errors`, con el campo y el mensaje
    por separado. El nombre del campo aquí es el identificador interno
    (`base_price`, `duration_months`), que no se le debe mostrar al usuario:
    es el frontend quien lo traduce a una etiqueta legible, porque es el que
    sabe cómo se llama ese campo en cada formulario. Sin esta parte
    estructurada el cliente solo recibía la cadena ya formateada y no le
    quedaba más remedio que enseñar el nombre de la variable.
    """
    errores = []
    detalles = []
    for err in exc.errors():
        campo = ".".join(str(p) for p in err.get("loc", []) if p not in ("body", "query"))
        mensaje = err.get("msg", "valor invalido")
        mensaje = mensaje.replace("Value error, ", "")
        errores.append(f"{campo}: {mensaje}" if campo else mensaje)
        detalles.append({"field": campo, "message": mensaje})

    return JSONResponse(
        status_code=422,
        content={
            "detail": {
                "code": "VALIDATION_ERROR",
                "message": " | ".join(errores) or "Datos inválidos.",
                "fields": errores,
                "errors": detalles,
            }
        },
    )


@app.exception_handler(asyncpg.PostgresError)
async def db_exception_handler(request: Request, exc: asyncpg.PostgresError):
    """Cualquier error de PostgreSQL no capturado antes se vuelve un 503."""
    logger.exception("Error de base de datos no controlado en %s", request.url.path)
    return JSONResponse(
        status_code=503,
        content=_error_body("DB_UNAVAILABLE", DB_UNAVAILABLE_MESSAGE),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Ultima red de seguridad: registra el error completo en el log del
    servidor y devuelve un mensaje generico, sin stacktrace ni detalles
    internos que puedan ayudar a un atacante.
    """
    logger.exception("Excepcion no controlada en %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content=_error_body("INTERNAL_ERROR", GENERIC_SERVER_MESSAGE),
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Endpoints de salud
# ---------------------------------------------------------------------------


@app.get("/")
async def root():
    return {"message": "Academia API v2.1 - FastAPI", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/test")
async def test_endpoint():
    return {
        "message": "Backend is running",
        "timestamp": datetime.now().isoformat(),
        "status": "ok",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "4000")),
        reload=True,
    )