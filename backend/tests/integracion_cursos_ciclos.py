"""
Pruebas de Integración (Frontend ↔ Backend ↔ BD) — Módulo Cursos y Ciclos
Estrategia Pressman, Cap. 17 - Sección 2.2 · Estrategia: Bottom-Up

Este NO es un test de PyTest: es un script ejecutable que corre los flujos de
integración contra el backend REAL (http://localhost:4000) y, por tanto, contra
la base de datos PostgreSQL de Railway. Imprime cada request/response con su
código de estado para usarlo como evidencia (captura de terminal).

Requisitos:
  1. Backend corriendo:   .venv/bin/python main.py
  2. Credenciales de admin de la BD (por defecto admin/admin123). Se pueden pasar
     por variables de entorno:  ADMIN_USER, ADMIN_PASS, API_URL

Uso:
  .venv/bin/python tests/integracion_cursos_ciclos.py
  ADMIN_USER=admin ADMIN_PASS=miclave .venv/bin/python tests/integracion_cursos_ciclos.py

Al final BORRA los datos de prueba que creó, para no ensuciar la BD del equipo.
"""
import os
import sys
import json
import httpx

API_URL = os.getenv("API_URL", "http://localhost:4000/api")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")

# Colores para la terminal (se ven bien en la captura)
OK = "\033[92m"      # verde
FAIL = "\033[91m"    # rojo
INFO = "\033[96m"    # cyan
DIM = "\033[90m"     # gris
END = "\033[0m"

passed = 0
failed = 0


def show(method: str, path: str, resp: httpx.Response, body=None):
    """Imprime la petición y la respuesta de forma legible."""
    print(f"{INFO}→ {method} {path}{END}")
    if body is not None:
        print(f"{DIM}  body: {json.dumps(body, ensure_ascii=False)}{END}")
    color = OK if resp.status_code < 400 else FAIL
    print(f"{color}← {resp.status_code} {resp.reason_phrase}{END}")
    try:
        data = resp.json()
        texto = json.dumps(data, ensure_ascii=False, indent=2)
        if len(texto) > 700:
            texto = texto[:700] + " ...(recortado)"
        print(f"{DIM}{texto}{END}")
    except Exception:
        print(f"{DIM}{resp.text[:300]}{END}")
    print()


def check(descripcion: str, condicion: bool):
    """Registra el resultado de una aserción de integración."""
    global passed, failed
    if condicion:
        passed += 1
        print(f"{OK}  ✓ {descripcion}{END}\n")
    else:
        failed += 1
        print(f"{FAIL}  ✗ {descripcion}{END}\n")


def main():
    print(f"\n{INFO}=== PRUEBAS DE INTEGRACIÓN · Cursos y Ciclos ==={END}")
    print(f"{DIM}API: {API_URL}{END}\n")

    cycle_id = None
    course_id = None
    offering_id = None

    with httpx.Client(timeout=30.0) as client:
        # -------------------------------------------------------------------
        # LOGIN — obtener token de admin
        # -------------------------------------------------------------------
        print(f"{INFO}── LOGIN (admin) ─────────────────────────────{END}")
        try:
            r = client.post(f"{API_URL}/auth/login",
                            json={"dni": ADMIN_USER, "password": ADMIN_PASS})
        except httpx.ConnectError:
            print(f"{FAIL}No se pudo conectar al backend. ¿Está corriendo "
                  f"'.venv/bin/python main.py'?{END}")
            sys.exit(1)

        show("POST", "/auth/login", r, {"dni": ADMIN_USER, "password": "******"})
        if r.status_code != 200:
            print(f"{FAIL}Login fallido. Revisa ADMIN_USER/ADMIN_PASS.{END}")
            sys.exit(1)

        token = r.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        check("Login admin devuelve token", bool(token))

        try:
            # ---------------------------------------------------------------
            # FLUJO 1 — Crear ciclo y verificar persistencia
            # ---------------------------------------------------------------
            print(f"{INFO}── FLUJO 1: Crear ciclo + verificar persistencia ──{END}")
            nuevo_ciclo = {
                "name": "Ciclo Prueba INT",
                "start_date": "2026-03-01",
                "end_date": "2026-07-31",
                "duration_months": 5,
                "status": "open",
            }
            r = client.post(f"{API_URL}/cycles", headers=headers, json=nuevo_ciclo)
            show("POST", "/cycles", r, nuevo_ciclo)
            check("POST /cycles responde 201", r.status_code == 201)
            cycle_id = r.json().get("id")

            r = client.get(f"{API_URL}/cycles")
            show("GET", "/cycles", r)
            existe = any(c.get("id") == cycle_id for c in r.json())
            check("El ciclo creado aparece en GET /cycles (persistió en la BD)", existe)

            # ---------------------------------------------------------------
            # FLUJO 2 — Curso → Oferta → leer con JOINs
            # ---------------------------------------------------------------
            print(f"{INFO}── FLUJO 2: Curso → Oferta → JOINs ──{END}")
            nuevo_curso = {"name": "Curso INT", "description": "prueba", "base_price": 150}
            r = client.post(f"{API_URL}/courses", headers=headers, json=nuevo_curso)
            show("POST", "/courses", r, nuevo_curso)
            check("POST /courses responde 201", r.status_code == 201)
            course_id = r.json().get("id")

            nueva_oferta = {
                "course_id": course_id,
                "cycle_id": cycle_id,
                "group_label": "A",
                "capacity": 30,
            }
            r = client.post(f"{API_URL}/courses/offerings", headers=headers, json=nueva_oferta)
            show("POST", "/courses/offerings", r, nueva_oferta)
            check("POST /courses/offerings responde 201", r.status_code == 201)
            offering_id = r.json().get("id")

            r = client.get(f"{API_URL}/courses/offerings/{cycle_id}")
            show("GET", f"/courses/offerings/{cycle_id}", r)
            ofertas = r.json()
            con_join = any(
                o.get("id") == offering_id and "course_name" in o and "cycle_name" in o
                for o in ofertas
            )
            check("La oferta trae course_name y cycle_name (los JOIN funcionan)", con_join)

            # ---------------------------------------------------------------
            # FLUJO 3 — Control de roles (caso negativo)
            # ---------------------------------------------------------------
            print(f"{INFO}── FLUJO 3: Seguridad / control de roles ──{END}")
            r = client.post(f"{API_URL}/cycles", json=nuevo_ciclo)  # SIN token
            show("POST", "/cycles (sin token)", r, nuevo_ciclo)
            check("POST /cycles sin token es rechazado (401/403)", r.status_code in (401, 403))

        finally:
            # ---------------------------------------------------------------
            # LIMPIEZA — borrar lo creado (no ensuciar la BD del equipo)
            # ---------------------------------------------------------------
            print(f"{INFO}── LIMPIEZA: borrar datos de prueba ──{END}")
            if offering_id:
                r = client.delete(f"{API_URL}/courses/offerings/{offering_id}", headers=headers)
                show("DELETE", f"/courses/offerings/{offering_id}", r)
            if course_id:
                r = client.delete(f"{API_URL}/courses/{course_id}", headers=headers)
                show("DELETE", f"/courses/{course_id}", r)
            if cycle_id:
                r = client.delete(f"{API_URL}/cycles/{cycle_id}", headers=headers)
                show("DELETE", f"/cycles/{cycle_id}", r)

    # -----------------------------------------------------------------------
    # RESUMEN
    # -----------------------------------------------------------------------
    total = passed + failed
    color = OK if failed == 0 else FAIL
    print(f"{color}=== RESULTADO: {passed}/{total} aserciones de integración OK ==={END}\n")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
