from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from enum import Enum


# ---------------------------------------------------------------------
# Dominio de estados del módulo de matrículas
# CORRECCIÓN: antes el estado viajaba como `str` libre; el endpoint
# PUT /enrollments/status aceptaba cualquier cadena y la persistía.
# ---------------------------------------------------------------------
class EnrollmentStatus(str, Enum):
    PENDIENTE = "pendiente"
    ACEPTADO = "aceptado"
    RECHAZADO = "rechazado"
    CANCELADO = "cancelado"
    FINALIZADO = "finalizado"   # estado ausente en el flujo original


class EnrollmentItemType(str, Enum):
    COURSE = "course"
    PACKAGE = "package"


# Máquina de estados explícita del módulo.
# Cualquier transición no declarada aquí es rechazada por el backend.
TRANSICIONES_VALIDAS = {
    EnrollmentStatus.PENDIENTE: {
        EnrollmentStatus.ACEPTADO,
        EnrollmentStatus.RECHAZADO,
        EnrollmentStatus.CANCELADO,
    },
    EnrollmentStatus.ACEPTADO: {
        EnrollmentStatus.FINALIZADO,
        EnrollmentStatus.CANCELADO,
    },
    EnrollmentStatus.RECHAZADO: {
        EnrollmentStatus.PENDIENTE,   # el estudiante vuelve a subir voucher
        EnrollmentStatus.CANCELADO,
    },
    EnrollmentStatus.CANCELADO: set(),    # estado terminal
    EnrollmentStatus.FINALIZADO: set(),   # estado terminal
}

ETIQUETAS_ESTADO = {
    EnrollmentStatus.PENDIENTE: "Pendiente de pago",
    EnrollmentStatus.ACEPTADO: "Aceptada",
    EnrollmentStatus.RECHAZADO: "Rechazada",
    EnrollmentStatus.CANCELADO: "Cancelada",
    EnrollmentStatus.FINALIZADO: "Finalizada",
}


class EnrollmentItem(BaseModel):
    type: EnrollmentItemType
    id: int = Field(..., gt=0, description="ID de la oferta (course_offering o package_offering)")


class EnrollmentCreate(BaseModel):
    items: List[EnrollmentItem] = Field(..., min_length=1, max_length=20)

    @field_validator("items")
    @classmethod
    def sin_items_repetidos(cls, v):
        """
        CORRECCIÓN: el controlador validaba duplicados contra la base de
        datos pero no dentro del propio envío. Un POST con
        [{course,5},{course,5}] creaba DOS matrículas del mismo curso,
        burlando el RF13.
        """
        vistos = set()
        for item in v:
            clave = (item.type, item.id)
            if clave in vistos:
                raise ValueError(
                    "La solicitud contiene el mismo curso o paquete más de una vez. "
                    "Revisa tu selección antes de confirmar."
                )
            vistos.add(clave)
        return v


class EnrollmentStatusUpdate(BaseModel):
    enrollment_id: int = Field(..., gt=0)
    status: EnrollmentStatus
    reason: Optional[str] = Field(
        None, max_length=500,
        description="Motivo del cambio. Obligatorio al rechazar o cancelar."
    )


class EnrollmentCancel(BaseModel):
    """
    CORRECCIÓN: la ruta /enrollments/cancel recibía `data: dict` sin
    esquema, por lo que FastAPI no validaba nada ni documentaba el
    contrato en /docs.
    """
    enrollment_id: int = Field(..., gt=0)
    reason: Optional[str] = Field(None, max_length=500)


# ---------------------------------------------------------------------
# Paquetes (sin cambios funcionales, solo validación de rangos)
# ---------------------------------------------------------------------
class PackageCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = None
    base_price: float = Field(..., gt=0)
    course_ids: Optional[List[int]] = None


class PackageUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = None
    base_price: Optional[float] = Field(None, gt=0)
    course_ids: Optional[List[int]] = None


class PackageOfferingCreate(BaseModel):
    package_id: int = Field(..., gt=0)
    cycle_id: int = Field(..., gt=0)
    group_label: Optional[str] = None
    price_override: Optional[float] = Field(None, gt=0)
    capacity: Optional[int] = Field(None, gt=0)
    course_offering_ids: Optional[List[int]] = None


class PackageOfferingUpdate(BaseModel):
    group_label: Optional[str] = None
    price_override: Optional[float] = Field(None, gt=0)


class PackageOfferingCourseAdd(BaseModel):
    course_offering_id: int = Field(..., gt=0)