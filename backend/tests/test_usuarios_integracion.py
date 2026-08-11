"""
Pruebas de integración (foco de conectividad) - Módulo de Usuarios
Probado por: Aracely Llancaya Tapia

IMPORTANTE: estas pruebas necesitan que el backend esté corriendo
(uvicorn main:app --reload --port 4000) y conectado a la base de datos real,
ya que verifican persistencia real en la BD.

Antes de correr, asegúrate de tener un usuario admin válido en tu BD y
ajusta ADMIN_DNI / ADMIN_PASSWORD abajo si es necesario.
"""
import pytest
import httpx
import random

BASE_URL = "http://localhost:4000/api"
ADMIN_DNI = "admin"
ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def admin_token():
    with httpx.Client(base_url=BASE_URL) as client:
        r = client.post("/auth/login", json={"dni": ADMIN_DNI, "password": ADMIN_PASSWORD})
        assert r.status_code == 200, f"No se pudo loguear como admin: {r.text}"
        return r.json()["token"]


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def random_dni():
    """Genera un DNI de 8 dígitos que casi seguro no existe en la BD."""
    return str(random.randint(10000000, 99999999))


def test_integracion_login_admin(admin_token):
    assert admin_token is not None and len(admin_token) > 10


def test_integracion_listar_estudiantes(auth_headers):
    with httpx.Client(base_url=BASE_URL) as client:
        r = client.get("/students", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


def test_integracion_obtener_estudiante_existente(auth_headers):
    with httpx.Client(base_url=BASE_URL) as client:
        lista = client.get("/students", headers=auth_headers).json()
        assert len(lista) > 0, "No hay estudiantes en la BD para probar"
        student_id = lista[0]["id"]
        r = client.get(f"/students/{student_id}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["id"] == student_id


def test_integracion_obtener_estudiante_inexistente(auth_headers):
    with httpx.Client(base_url=BASE_URL) as client:
        r = client.get("/students/999999", headers=auth_headers)
        assert r.status_code == 404


def test_integracion_crear_estudiante(random_dni):
    with httpx.Client(base_url=BASE_URL) as client:
        payload = {
            "dni": random_dni,
            "first_name": "Test",
            "last_name": "Integracion",
            "phone": "987654321",
            "parent_name": "Padre Test",
            "parent_phone": "987654322",
            "password": random_dni,
        }
        r = client.post("/students/register", json=payload)
        assert r.status_code == 201


def test_integracion_estudiante_dni_duplicado(random_dni):
    with httpx.Client(base_url=BASE_URL) as client:
        payload = {
            "dni": random_dni,  # mismo DNI ya creado en el test anterior
            "first_name": "Test",
            "last_name": "Duplicado",
            "phone": "987654321",
            "parent_name": "Padre Test",
            "parent_phone": "987654322",
            "password": random_dni,
        }
        r = client.post("/students/register", json=payload)
        assert r.status_code == 400


def test_integracion_actualizar_estudiante(auth_headers, random_dni):
    with httpx.Client(base_url=BASE_URL) as client:
        lista = client.get("/students", headers=auth_headers).json()
        estudiante = next(s for s in lista if s["dni"] == random_dni)
        r = client.put(
            f"/students/{estudiante['id']}",
            headers=auth_headers,
            json={"phone": "999888777"},
        )
        assert r.status_code == 200

        verificacion = client.get(f"/students/{estudiante['id']}", headers=auth_headers)
        assert verificacion.json()["phone"] == "999888777"


def test_integracion_eliminar_estudiante(auth_headers, random_dni):
    with httpx.Client(base_url=BASE_URL) as client:
        lista = client.get("/students", headers=auth_headers).json()
        estudiante = next(s for s in lista if s["dni"] == random_dni)
        r = client.delete(f"/students/{estudiante['id']}", headers=auth_headers)
        assert r.status_code == 200


def test_integracion_listar_docentes(auth_headers):
    with httpx.Client(base_url=BASE_URL) as client:
        r = client.get("/teachers", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


def test_integracion_crear_docente(auth_headers, random_dni):
    with httpx.Client(base_url=BASE_URL) as client:
        payload = {
            "first_name": "Test",
            "last_name": "Docente",
            "dni": random_dni,
            "phone": "987654321",
            "email": "test.docente@academia.edu.pe",
            "specialization": "Prueba",
        }
        r = client.post("/teachers", headers=auth_headers, json=payload)
        # Con el fix de BG-U1 aplicado, debe responder 201 si el DNI es nuevo
        assert r.status_code == 201


def test_integracion_docente_dni_duplicado(auth_headers, random_dni):
    with httpx.Client(base_url=BASE_URL) as client:
        payload = {
            "first_name": "Test",
            "last_name": "Docente Duplicado",
            "dni": random_dni,  # mismo DNI del test anterior
            "phone": "987654321",
            "email": "otro@academia.edu.pe",
            "specialization": "Prueba",
        }
        r = client.post("/teachers", headers=auth_headers, json=payload)
        # Antes del fix de BG-U1 esto fallaba devolviendo 201 con {"error": ...}
        assert r.status_code == 400


def test_integracion_resetear_password_docente(auth_headers, random_dni):
    with httpx.Client(base_url=BASE_URL) as client:
        lista = client.get("/teachers", headers=auth_headers).json()
        docente = next(t for t in lista if t["dni"] == random_dni)
        r = client.post(f"/teachers/{docente['id']}/reset-password", headers=auth_headers)
        assert r.status_code == 200


def test_integracion_eliminar_docente(auth_headers, random_dni):
    with httpx.Client(base_url=BASE_URL) as client:
        lista = client.get("/teachers", headers=auth_headers).json()
        docente = next(t for t in lista if t["dni"] == random_dni)
        r = client.delete(f"/teachers/{docente['id']}", headers=auth_headers)
        assert r.status_code == 200


def test_integracion_dashboard_admin(auth_headers):
    with httpx.Client(base_url=BASE_URL) as client:
        r = client.get("/admin/dashboard", headers=auth_headers)
        assert r.status_code == 200


def test_integracion_estadisticas_admin(auth_headers):
    with httpx.Client(base_url=BASE_URL) as client:
        r = client.get("/admin/stats", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert "total_students" in data
        assert "total_teachers" in data