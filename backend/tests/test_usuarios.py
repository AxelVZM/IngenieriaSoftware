"""
Pruebas unitarias (caja blanca) - Módulo de Usuarios
Probado por: Aracely Llancaya Tapia

Cubre las funciones críticas de studentController.py y teacherController.py,
usando mocks para no depender de una base de datos real.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from controllers import studentController, teacherController
from models.student import StudentCreate, StudentUpdate
from models.teacher import TeacherCreate


def make_record(data: dict):
    """Simula un asyncpg.Record: se comporta como dict al hacer dict(record)."""
    m = MagicMock()
    m.__getitem__.side_effect = data.__getitem__
    m.keys.side_effect = data.keys
    return data  # dict(data) funciona igual que dict(Record) en los controllers


# ---------- ESTUDIANTES ----------

@pytest.mark.asyncio
async def test_get_all_students():
    db = AsyncMock()
    db.fetch.return_value = [
        {"id": 1, "dni": "72900067", "first_name": "Pamela", "last_name": "Diaz"}
    ]
    result = await studentController.get_all_students(db)
    assert len(result) == 1
    assert result[0]["dni"] == "72900067"


@pytest.mark.asyncio
async def test_get_student_by_id_existe():
    db = AsyncMock()
    db.fetchrow.return_value = {"id": 1, "dni": "72900067", "first_name": "Pamela"}
    result = await studentController.get_student_by_id(1, db)
    assert result["id"] == 1


@pytest.mark.asyncio
async def test_get_student_by_id_no_existe():
    db = AsyncMock()
    db.fetchrow.return_value = None
    result = await studentController.get_student_by_id(9999, db)
    assert result is None


@pytest.mark.asyncio
async def test_create_student_exitoso():
    db = AsyncMock()
    db.fetchrow.side_effect = [None, {"id": 10}]  # 1) no existe DNI  2) insert devuelve id
    data = StudentCreate(
        dni="99509786", first_name="Test", last_name="Student",
        phone="987654321", parent_name="Padre Test", parent_phone="987654322",
        password="99509786"
    )
    result = await studentController.create_student(data, db)
    assert result["id"] == 10
    assert "message" in result


@pytest.mark.asyncio
async def test_create_student_dni_duplicado():
    db = AsyncMock()
    db.fetchrow.return_value = {"id": 5}  # el DNI ya existe
    data = StudentCreate(
        dni="72900067", first_name="Test", last_name="Student",
        phone="987654321", parent_name="Padre Test", parent_phone="987654322",
        password="72900067"
    )
    result = await studentController.create_student(data, db)
    assert "error" in result
    assert "ya se encuentra registrado" in result["error"]


@pytest.mark.asyncio
async def test_update_student():
    db = AsyncMock()
    data = StudentUpdate(phone="999888777")
    result = await studentController.update_student(1, data, db)
    db.execute.assert_awaited_once()
    assert result["message"] == "Estudiante actualizado correctamente"


@pytest.mark.asyncio
async def test_update_student_sin_campos():
    db = AsyncMock()
    data = StudentUpdate()
    result = await studentController.update_student(1, data, db)
    db.execute.assert_not_called()
    assert result["message"] == "No hay campos para actualizar"


@pytest.mark.asyncio
async def test_delete_student():
    db = AsyncMock()
    db.fetchval.return_value = 0  # simula que no tiene matriculas ni asistencias
    result = await studentController.delete_student(1, db)
    db.execute.assert_awaited_once()
    assert result["message"] == "Estudiante eliminado correctamente"


# ---------- DOCENTES ----------

@pytest.mark.asyncio
async def test_get_all_teachers():
    db = AsyncMock()
    db.fetch.return_value = [
        {"id": 1, "dni": "75507932", "first_name": "Javier", "last_name": "Cruz"}
    ]
    result = await teacherController.get_all_teachers(db)
    assert len(result) == 1
    assert result[0]["name"] == "Javier Cruz"  # campo 'name' compuesto para el frontend


@pytest.mark.asyncio
async def test_get_teacher_by_id_existe():
    db = AsyncMock()
    db.fetchrow.return_value = {"id": 1, "dni": "75507932", "first_name": "Javier"}
    result = await teacherController.get_teacher_by_id(1, db)
    assert result["id"] == 1


@pytest.mark.asyncio
async def test_get_teacher_by_id_no_existe():
    db = AsyncMock()
    db.fetchrow.return_value = None
    result = await teacherController.get_teacher_by_id(9999, db)
    assert result is None


@pytest.mark.asyncio
async def test_create_teacher_exitoso():
    db = AsyncMock()
    db.fetchrow.side_effect = [
        None,               # DNI no existe
        {"id": 20},         # INSERT INTO users devuelve id
        {"id": 30},         # INSERT INTO teachers devuelve id
    ]
    data = TeacherCreate(
        first_name="Mario", last_name="Fernandez", dni="45789652",
        phone="985632145", email="mafe@gmail.com", specialization="Fisica"
    )
    result = await teacherController.create_teacher(data, db)
    assert result["id"] == 30
    assert "message" in result


@pytest.mark.asyncio
async def test_create_teacher_dni_duplicado():
    db = AsyncMock()
    db.fetchrow.return_value = {"id": 1}  # el DNI ya existe
    data = TeacherCreate(
        first_name="Mario", last_name="Fernandez", dni="75507932",
        phone="985632145", email="mafe@gmail.com", specialization="Fisica"
    )
    result = await teacherController.create_teacher(data, db)
    assert "error" in result
    assert "ya se encuentra registrado" in result["error"]


@pytest.mark.asyncio
async def test_delete_teacher():
    db = AsyncMock()
    db.fetchval.return_value = 0  # simula que no tiene ofertas asignadas
    db.execute.return_value = "DELETE 1"  # simula que sí borró un registro
    result = await teacherController.delete_teacher(1, db)
    db.execute.assert_awaited_once()
    assert "message" in result