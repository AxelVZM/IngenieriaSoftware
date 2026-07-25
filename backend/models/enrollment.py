from pydantic import BaseModel
from typing import Optional, List

class EnrollmentItem(BaseModel):
    type: str  # 'course' or 'package'
    id: int

class EnrollmentCreate(BaseModel):
    items: List[EnrollmentItem]

class EnrollmentStatusUpdate(BaseModel):
    enrollment_id: int
    status: str

class PackageCreate(BaseModel):
    name: str
    description: Optional[str] = None
    base_price: float
    course_ids: Optional[List[int]] = None

class PackageUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: Optional[float] = None
    course_ids: Optional[List[int]] = None

class PackageOfferingCreate(BaseModel):
    package_id: int
    cycle_id: int
    group_label: Optional[str] = None
    price_override: Optional[float] = None
    capacity: Optional[int] = None
    course_offering_ids: Optional[List[int]] = None

class PackageOfferingUpdate(BaseModel):
    group_label: Optional[str] = None
    price_override: Optional[float] = None

class PackageOfferingCourseAdd(BaseModel):
    course_offering_id: int
