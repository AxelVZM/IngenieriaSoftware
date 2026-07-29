import requests
import sys
import time
import random

# Códigos de color ANSI
GREEN = '\033[92m'
RED = '\033[91m'
CYAN = '\033[96m'
GRAY = '\033[90m'
RESET = '\033[0m'

BASE_URL = "http://127.0.0.1:4000/api"

def print_header():
    print("======================================================================")
    print("PRUEBAS DE FUNCIÓN (REALES) - Módulo de Cursos y Ciclos (Extendidas)")
    print(f"Backend: {BASE_URL}")
    print("======================================================================")
    print("")

def run_test(id, desc, expected_status, method, endpoint, headers=None, json=None):
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "POST":
            response = requests.post(url, headers=headers, json=json)
        elif method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=json)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
            
        status_code = response.status_code
        
        passed = (status_code == expected_status)
        
        if passed:
            sys.stdout.write(f" [{GREEN}PASA{RESET}] {id}  {desc}\n")
        else:
            sys.stdout.write(f" [{RED}FALLA{RESET}] {id}  {desc} (Esp: {expected_status}, Rec: {status_code})\n")
        
        extra = ""
        try:
            data = response.json()
            if 'detail' in data:
                extra = f"detail={str(data['detail'])[:80]}..."
            elif 'error' in data:
                extra = f"error={str(data['error'])[:80]}..."
            elif 'message' in data:
                extra = f"message={str(data['message'])[:80]}"
        except:
            extra = "Sin cuerpo JSON"
            
        sys.stdout.write(f"          {GRAY}status={status_code} {extra}{RESET}\n")
        return response, passed
        
    except requests.exceptions.ConnectionError:
        print(f"{RED}Error: No se pudo conectar a {url}. ¿Está levantado el backend?{RESET}")
        sys.exit(1)

def main():
    print_header()
    
    # 1. Autenticación como admin
    print(f"{GRAY}Intentando login como admin...{RESET}")
    login_res = requests.post(f"{BASE_URL}/auth/login", json={"dni": "admin", "password": "admin123"})
    if login_res.status_code != 200:
        print(f"{RED}Error crítico: No se pudo iniciar sesión como admin.{RESET}")
        sys.exit(1)
        
    token = login_res.json().get("access_token", login_res.json().get("token"))
    headers = {"Authorization": f"Bearer {token}"}
    print(f"{GREEN}Login exitoso.{RESET}\n")
    
    print(f"{CYAN}RF01 - Gestión Completa de Ciclos Académicos{RESET}")
    
    # CF-01: Listar ciclos
    run_test("CF-01", "Listar todos los ciclos académicos", 200, "GET", "/cycles", headers=headers)
    
    # CF-02: Crear ciclo válido
    rand_id = random.randint(1000, 9999)
    payload_valido = {
        "name": f"Ciclo Test {rand_id}",
        "start_date": "2026-10-01",
        "end_date": "2026-12-01",
        "duration_months": 3,
        "status": "open"
    }
    res_crear, _ = run_test("CF-02", "Creación de ciclo con datos válidos", 201, "POST", "/cycles", headers=headers, json=payload_valido)
    cycle_id = res_crear.json().get("id") if res_crear.status_code == 201 else None

    # CF-03: Actualizar ciclo
    if cycle_id:
        payload_update = {"name": f"Ciclo Actualizado {rand_id}"}
        run_test("CF-03", "Actualización de nombre de ciclo", 200, "PUT", f"/cycles/{cycle_id}", headers=headers, json=payload_update)

    # CF-04: Fechas inconsistentes (ahora con modelo arreglado)
    payload_invalido = {
        "name": "Ciclo Fechas Mal",
        "start_date": "2026-12-01",
        "end_date": "2026-10-01",
        "duration_months": 3
    }
    run_test("CF-04", "Fechas inconsistentes (fin < inicio) son rechazadas", 422, "POST", "/cycles", headers=headers, json=payload_invalido)
    
    # CF-05: Falta un campo obligatorio
    payload_incompleto = {
        "start_date": "2026-10-01",
        "end_date": "2026-12-01",
        "duration_months": 3
    }
    run_test("CF-05", "Falta un campo obligatorio (nombre)", 422, "POST", "/cycles", headers=headers, json=payload_incompleto)
    
    # CF-06: Obtener ciclo activo
    run_test("CF-06", "Obtener el ciclo activo actual", 200, "GET", "/cycles/active", headers=headers)
    
    print("")
    print(f"{CYAN}RF02 - Gestión Completa de Cursos (Maestros){RESET}")
    
    # CF-07: Crear curso válido
    course_payload = {
        "name": f"Curso QA {rand_id}",
        "description": "Pruebas de software avanzadas",
        "base_price": 100.50
    }
    res_course, _ = run_test("CF-07", "Creación de curso (master) válido", 201, "POST", "/courses", headers=headers, json=course_payload)
    course_id = res_course.json().get("id") if res_course.status_code == 201 else None

    # CF-08: Actualizar curso
    if course_id:
        course_update = {"base_price": 150.00}
        run_test("CF-08", "Actualización de precio base del curso", 200, "PUT", f"/courses/{course_id}", headers=headers, json=course_update)

    # CF-09: Precio negativo rechazado
    course_negativo = {
        "name": "Curso Negativo",
        "base_price": -50.0
    }
    run_test("CF-09", "Precio base negativo o nulo no permitido", 422, "POST", "/courses", headers=headers, json=course_negativo)

    # CF-10: Listar cursos
    run_test("CF-10", "Listar catálogo general de cursos", 200, "GET", "/courses", headers=headers)

    print("")
    print(f"{CYAN}RF03 - Eliminaciones y Cascadas{RESET}")
    if course_id:
        run_test("CF-11", "Eliminación de curso (master) exitosa", 200, "DELETE", f"/courses/{course_id}", headers=headers)
    if cycle_id:
        run_test("CF-12", "Eliminación de ciclo (vacío) exitosa", 200, "DELETE", f"/cycles/{cycle_id}", headers=headers)

if __name__ == "__main__":
    main()
