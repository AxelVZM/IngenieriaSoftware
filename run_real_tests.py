import requests
import sys
import random

GREEN = '\033[92m'
RED = '\033[91m'
CYAN = '\033[96m'
GRAY = '\033[90m'
RESET = '\033[0m'

BASE_URL = "http://127.0.0.1:4000/api"

# Conteo global para el resumen final (evidencia de la auditoría)
resultados = {"pasa": 0, "falla": 0}

def print_header():
    print("======================================================================")
    print("PRUEBAS DE FUNCIÓN (REALES) - Módulo de Cursos y Ciclos (Extendidas)")
    print(f"Backend: {BASE_URL}")
    print("======================================================================")
    print("")

def run_test(id, desc, expected_status, method, endpoint, headers=None, json=None,
             expect_text=None):
    """Ejecuta un caso de prueba de función.

    expected_status: código esperado (int) o lista de códigos aceptables.
    expect_text:     además del código, verifica el CONTENIDO de la respuesta.
                     Sirve para las pruebas de contenido a nivel de API: que el
                     mensaje esté en español, sea explicativo y no una traza.
    """
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
        passed = (status_code == expected_status or (type(expected_status) == list and status_code in expected_status))

        # Prueba de contenido: el texto que el usuario terminará viendo
        contenido_ok = True
        if expect_text is not None:
            contenido_ok = expect_text.lower() in response.text.lower()
            passed = passed and contenido_ok

        resultados["pasa" if passed else "falla"] += 1

        if passed:
            sys.stdout.write(f" [{GREEN}PASA{RESET}] {id}  {desc}\n")
        elif not contenido_ok:
            sys.stdout.write(f" [{RED}FALLA{RESET}] {id}  {desc} (Falta el texto esperado: '{expect_text}')\n")
        else:
            exp_str = expected_status if not isinstance(expected_status, list) else ' o '.join(map(str, expected_status))
            sys.stdout.write(f" [{RED}FALLA{RESET}] {id}  {desc} (Esp: {exp_str}, Rec: {status_code})\n")

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
    
    print(f"{GRAY}Intentando login como admin...{RESET}")
    login_res = requests.post(f"{BASE_URL}/auth/login", json={"dni": "admin", "password": "admin123"})
    if login_res.status_code != 200:
        print(f"{RED}Error crítico: No se pudo iniciar sesión como admin.{RESET}")
        sys.exit(1)
        
    token = login_res.json().get("access_token", login_res.json().get("token"))
    headers = {"Authorization": f"Bearer {token}"}
    print(f"{GREEN}Login exitoso.{RESET}\n")
    
    print(f"{CYAN}RF01 - Gestión Completa de Ciclos Académicos{RESET}")
    run_test("CF-01", "Listar todos los ciclos académicos", 200, "GET", "/cycles", headers=headers)
    
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

    if cycle_id:
        payload_update = {"name": f"Ciclo Actualizado {rand_id}"}
        run_test("CF-03", "Actualización de nombre de ciclo", 200, "PUT", f"/cycles/{cycle_id}", headers=headers, json=payload_update)

    payload_invalido = {
        "name": "Ciclo Fechas Mal",
        "start_date": "2026-12-01",
        "end_date": "2026-10-01",
        "duration_months": 3
    }
    run_test("CF-04", "Fechas inconsistentes (fin < inicio) son rechazadas", 422, "POST", "/cycles", headers=headers, json=payload_invalido)
    
    payload_incompleto = {
        "start_date": "2026-10-01",
        "end_date": "2026-12-01",
        "duration_months": 3
    }
    run_test("CF-05", "Falta un campo obligatorio (nombre)", 422, "POST", "/cycles", headers=headers, json=payload_incompleto)
    
    # Nuevos casos reales basados en el código
    # CF-05B: Duración negativa o 0
    payload_duracion_invalida = {
        "name": "Ciclo Duración Cero",
        "start_date": "2026-10-01",
        "end_date": "2026-12-01",
        "duration_months": 0
    }
    run_test("CF-05B", "Duración del ciclo igual o menor a cero es rechazada", 422, "POST", "/cycles", headers=headers, json=payload_duracion_invalida)

    # CF-05C: Ciclo duplicado (¿El backend maneja el error de base de datos amigablemente o lanza 500?)
    if cycle_id:
        # Intentamos crear otro con el mismo nombre exacto a ver qué hace la base de datos (si hay unique constraint)
        # Si no hay constraint, pasará (201). Si hay y no se maneja, dará 500.
        pass # Skip para no ensuciar la bd si no hay constraint, ya que no vimos UNIQUE en los modelos, depende de la BD.

    run_test("CF-06", "Obtener el ciclo activo actual", 200, "GET", "/cycles/active", headers=headers)
    
    print("")
    print(f"{CYAN}RF02 - Gestión Completa de Cursos (Maestros){RESET}")
    
    course_payload = {
        "name": f"Curso QA {rand_id}",
        "description": "Pruebas de software avanzadas",
        "base_price": 100.50
    }
    res_course, _ = run_test("CF-07", "Creación de curso (master) válido", 201, "POST", "/courses", headers=headers, json=course_payload)
    course_id = res_course.json().get("id") if res_course.status_code == 201 else None

    if course_id:
        course_update = {"base_price": 150.00}
        run_test("CF-08", "Actualización de precio base del curso", 200, "PUT", f"/courses/{course_id}", headers=headers, json=course_update)

    course_negativo = {
        "name": "Curso Negativo",
        "base_price": -50.0
    }
    run_test("CF-09", "Precio base negativo no permitido", 422, "POST", "/courses", headers=headers, json=course_negativo)

    run_test("CF-10", "Listar catálogo general de cursos", 200, "GET", "/courses", headers=headers)

    print("")
    print(f"{CYAN}RF03 - Casos Complejos y Cascadas{RESET}")
    
    # Vamos a intentar asignar un curso a un ciclo (crear un course_offering)
    if course_id and cycle_id:
        offering_payload = {
            "course_id": course_id,
            "cycle_id": cycle_id,
            "group_label": "Grupo A",
            "capacity": 30
        }
        res_off, _ = run_test("CF-11", "Asignar curso a un ciclo (Course Offering)", 201, "POST", "/courses/offerings", headers=headers, json=offering_payload)
        offering_id = res_off.json().get("id") if res_off.status_code == 201 else None
        
        # Ahora intentamos eliminar el curso padre que tiene un offering
        # Si la base de datos tiene una foreign key restrict, esto debería dar error. Si el backend no lo captura bien, dará error 500.
        # Esperamos idealmente un 400 (Bad Request) o 409 (Conflict), pero si da 500 es un bug semántico a reportar.
        run_test("CF-12", "Intentar eliminar un curso que tiene un offering asociado (Debe fallar limpiamente)", [400, 409, 422], "DELETE", f"/courses/{course_id}", headers=headers)
        
        # Limpiamos el offering
        if offering_id:
            requests.delete(f"{BASE_URL}/courses/offerings/{offering_id}", headers=headers)

    # Limpieza normal
    if course_id:
        run_test("CF-13", "Eliminación de curso sin dependencias exitosa", 200, "DELETE", f"/courses/{course_id}", headers=headers)
    if cycle_id:
        run_test("CF-14", "Eliminación de ciclo vacío exitosa", 200, "DELETE", f"/cycles/{cycle_id}", headers=headers)

    # -------------------------------------------------------------------
    # RF04 - Auditoría de función: casos que la matriz original no cubría.
    # El "expected_status" es el comportamiento CORRECTO, así que un [FALLA]
    # aquí es la evidencia de un defecto abierto, no un error del script.
    # -------------------------------------------------------------------
    print("")
    print(f"{CYAN}RF04 - Auditoría de función: ids inexistentes, validación y autorización{RESET}")

    run_test("CF-15", "GET de un ciclo inexistente devuelve 404", 404,
             "GET", "/cycles/99999999", headers=headers)
    run_test("CF-16", "PUT sobre un ciclo inexistente debe devolver 404 [DEF-04]", 404,
             "PUT", "/cycles/99999999", headers=headers, json={"name": "Ciclo Fantasma"})
    run_test("CF-17", "PUT sobre un curso inexistente debe devolver 404 [DEF-04]", 404,
             "PUT", "/courses/99999999", headers=headers, json={"base_price": 99.0})
    # Ojo: mientras DEF-03 siga abierto este POST tiene ÉXITO, así que hay que
    # borrar el curso que deja creado para no ensuciar la base de datos.
    res_cero, _ = run_test("CF-18", "Precio base en CERO debe ser rechazado [DEF-03]", 422,
                           "POST", "/courses", headers=headers,
                           json={"name": f"Curso Gratis {rand_id}", "base_price": 0})
    if res_cero.status_code == 201:
        requests.delete(f"{BASE_URL}/courses/{res_cero.json().get('id')}", headers=headers)
    run_test("CF-19", "Fecha de fin IGUAL a la de inicio es rechazada", 422,
             "POST", "/cycles", headers=headers,
             json={"name": "Ciclo Cero Dias", "start_date": "2026-10-01",
                   "end_date": "2026-10-01", "duration_months": 1})
    run_test("CF-20", "POST /courses sin token es rechazado", [401, 403],
             "POST", "/courses", json={"name": "Curso Sin Token", "base_price": 100.0})

    # -------------------------------------------------------------------
    # RF05 - Prueba de CONTENIDO a nivel de API: además del código de estado
    # se verifica el TEXTO que el usuario terminará leyendo en la pantalla.
    # -------------------------------------------------------------------
    print("")
    print(f"{CYAN}RF05 - Contenido de las respuestas (mensajes al usuario){RESET}")

    aud_cycle_id = None
    aud_course_id = None
    aud_offering_id = None

    res, _ = run_test("CF-21", "El mensaje de creación es explicativo y está en español", 201,
                      "POST", "/cycles", headers=headers,
                      json={"name": f"Ciclo Contenido {rand_id}", "start_date": "2027-03-01",
                            "end_date": "2027-07-31", "duration_months": 5, "status": "in_progress"},
                      expect_text="Ciclo creado exitosamente")
    if res.status_code == 201:
        aud_cycle_id = res.json().get("id")

    run_test("CF-22", "El 404 devuelve un mensaje legible, no una traza", 404,
             "GET", "/cycles/99999999", headers=headers,
             expect_text="Ciclo no encontrado")

    res, _ = run_test("CF-23", "Creación de curso para las pruebas de cascada", 201,
                      "POST", "/courses", headers=headers,
                      json={"name": f"Curso Contenido {rand_id}", "base_price": 200.0})
    if res.status_code == 201:
        aud_course_id = res.json().get("id")

    if aud_cycle_id and aud_course_id:
        res = requests.post(f"{BASE_URL}/courses/offerings", headers=headers, json={
            "course_id": aud_course_id, "cycle_id": aud_cycle_id,
            "group_label": "Grupo Aud", "capacity": 20})
        if res.status_code == 201:
            aud_offering_id = res.json().get("id")

        # El mensaje de bloqueo debe explicar la CAUSA, no solo negarse.
        run_test("CF-24", "El bloqueo por dependencias explica la causa al usuario", 409,
                 "DELETE", f"/cycles/{aud_cycle_id}", headers=headers,
                 expect_text="No se puede eliminar")

    # Limpieza de las fixtures (en orden inverso de dependencia)
    if aud_offering_id:
        requests.delete(f"{BASE_URL}/courses/offerings/{aud_offering_id}", headers=headers)
    if aud_course_id:
        requests.delete(f"{BASE_URL}/courses/{aud_course_id}", headers=headers)
    if aud_cycle_id:
        requests.delete(f"{BASE_URL}/cycles/{aud_cycle_id}", headers=headers)

    # -------------------------------------------------------------------
    # RESUMEN
    # -------------------------------------------------------------------
    total = resultados["pasa"] + resultados["falla"]
    color = GREEN if resultados["falla"] == 0 else RED
    print("")
    print("======================================================================")
    print(f"{color}RESUMEN: {resultados['pasa']}/{total} casos con el resultado esperado "
          f"({resultados['falla']} defecto(s) abierto(s)){RESET}")
    print("======================================================================")

if __name__ == "__main__":
    main()
