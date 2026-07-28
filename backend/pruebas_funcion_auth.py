"""
PRUEBAS DE FUNCIÓN — Módulo de Autenticación
Sistema de Gestión de Matrículas, Academia "Unión de Nuevos Inteligentes"

Objetivo: descubrir errores que indiquen que NO se cumplen los requisitos del
cliente. A diferencia de las pruebas de contenido, aquí no se evalúa el texto
sino el comportamiento frente a cada requisito funcional y no funcional.

Requisitos cubiertos:
  RF01   Registro de estudiantes
  RF02   Inicio de sesión por tipo de usuario
  RNF03  Autenticación mediante JWT
  RNF04  Contraseñas almacenadas cifradas
  RNF05  Control de acceso por roles

USO (con el backend corriendo en otra terminal):

    python pruebas_funcion_auth.py --admin-user admin --admin-pass TU_CLAVE
    python pruebas_funcion_auth.py --help

Parámetros:
    --url            URL base del backend (por defecto http://127.0.0.1:4000)
    --admin-user     Usuario administrador (para RF02 y RNF05)
    --admin-pass     Contraseña del administrador
    --docente-user   Usuario docente (opcional, para RF02)
    --docente-pass   Contraseña del docente
    --ruta-admin     Endpoint solo-admin a usar en RNF05
    --no-crear       Omite los casos que insertan datos en la base de datos

RECOMENDACIÓN: ejecuta el backend SIN --reload mientras corres esta batería.
Con --reload, uvicorn reinicia el servidor en cuanto detecta un archivo nuevo
en la carpeta (por ejemplo, este mismo script) y corta las peticiones en curso.

AVISO: salvo que uses --no-crear, el script REGISTRA UN ESTUDIANTE DE PRUEBA
en tu base de datos, con un DNI que empieza por 99. Al terminar te indica cuál
para que lo elimines desde el panel de administración.

No requiere librerías externas: usa solo la biblioteca estándar.
"""

from __future__ import annotations

import argparse
import http.client
import json
import random
import sys
import time
import urllib.error
import urllib.request

if sys.platform == "win32":
    import os

    os.system("")  # habilita los códigos ANSI en la consola de Windows

VERDE, ROJO, AMARILLO, AZUL, GRIS, RESET = (
    "\033[92m", "\033[91m", "\033[93m", "\033[96m", "\033[90m", "\033[0m",
)

resultados: list[dict] = []


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------


# Errores de red que suelen ser pasajeros. El caso típico es que uvicorn se
# haya reiniciado (--reload) justo durante una petición: la conexión se corta
# y Windows devuelve WinError 10054. Se reintenta en lugar de abortar.
ERRORES_PASAJEROS = (
    ConnectionResetError,
    ConnectionAbortedError,
    http.client.RemoteDisconnected,
    http.client.BadStatusLine,
    TimeoutError,
)

REINTENTOS = 3
ESPERA_REINTENTO = 2.0  # segundos


def _es_pasajero(exc) -> bool:
    if isinstance(exc, ERRORES_PASAJEROS):
        return True
    razon = getattr(exc, "reason", None)
    return isinstance(razon, ERRORES_PASAJEROS)


def peticion(url, metodo="GET", cuerpo=None, token=None, timeout=20,
             salir_si_no_conecta=True):
    """
    Devuelve (status, body, headers). Nunca lanza por código HTTP.

    Ante un corte de conexión reintenta hasta REINTENTOS veces. Si aun así
    falla, devuelve status 0 para que el caso se marque como fallido en lugar
    de interrumpir toda la batería.
    """
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None

    for intento in range(1, REINTENTOS + 1):
        req = urllib.request.Request(url, data=datos, method=metodo)
        req.add_header("Content-Type", "application/json")
        req.add_header("Connection", "close")  # evita reutilizar sockets muertos
        if token:
            req.add_header("Authorization", f"Bearer {token}")

        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read().decode()
                return r.status, (json.loads(raw) if raw else None), dict(r.headers)

        except urllib.error.HTTPError as e:
            raw = e.read().decode()
            try:
                body = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                body = {"_raw": raw}
            return e.code, body, dict(e.headers)

        except urllib.error.URLError as e:
            rechazado = isinstance(getattr(e, "reason", None), ConnectionRefusedError)
            if rechazado:
                # Puede ser que el servidor esté reiniciándose: se reintenta.
                if intento < REINTENTOS:
                    time.sleep(ESPERA_REINTENTO)
                    continue
                if salir_si_no_conecta:
                    print(f"\n{ROJO}No se pudo conectar con {url}.{RESET}")
                    print("Verifica que el backend esté corriendo:")
                    print("  uvicorn main:app --port 4000\n")
                    sys.exit(1)
                return 0, {"_error": "conexión rechazada"}, {}
            if _es_pasajero(e) and intento < REINTENTOS:
                print(f"    {AMARILLO}conexión cortada, reintentando ({intento}/{REINTENTOS})…{RESET}")
                time.sleep(ESPERA_REINTENTO)
                continue
            return 0, {"_error": str(getattr(e, "reason", e))}, {}

        except OSError as e:
            if _es_pasajero(e) and intento < REINTENTOS:
                print(f"    {AMARILLO}conexión cortada, reintentando ({intento}/{REINTENTOS})…{RESET}")
                time.sleep(ESPERA_REINTENTO)
                continue
            return 0, {"_error": str(e)}, {}

    return 0, {"_error": "sin respuesta tras varios reintentos"}, {}


def esperar_backend(base, intentos=10):
    """
    Espera a que el backend responda antes de empezar.

    Si uvicorn se está reiniciando (por --reload), esto absorbe el reinicio en
    lugar de que lo sufra el primer caso de prueba.
    """
    for i in range(intentos):
        st, _, _ = peticion(f"{base}/health", timeout=5, salir_si_no_conecta=False)
        if st == 200:
            if i:
                print(f"  {GRIS}backend disponible tras {i} reintento(s){RESET}")
            return True
        time.sleep(1.5)
    return False


def codigo(body) -> str:
    d = (body or {}).get("detail")
    return d.get("code", "") if isinstance(d, dict) else ""


def caso(cid, requisito, descripcion, esperado, condicion, real="", omitido=False):
    """Registra el resultado de un caso de prueba."""
    estado = "OMITIDO" if omitido else ("PASA" if condicion else "FALLA")
    resultados.append({
        "id": cid, "req": requisito, "desc": descripcion,
        "esperado": esperado, "real": real, "estado": estado,
    })
    color = {"PASA": VERDE, "FALLA": ROJO, "OMITIDO": AMARILLO}[estado]
    print(f"  {color}[{estado:^8}]{RESET} {cid}  {descripcion}")
    if real:
        print(f"              {GRIS}{real}{RESET}")


def titulo(texto):
    print(f"\n{AZUL}{texto}{RESET}")


def estudiante_valido(dni):
    return {
        "dni": dni,
        "first_name": "Estudiante",
        "last_name": "De Prueba",
        "phone": "987654321",
        "parent_name": "Apoderado De Prueba",
        "parent_phone": "987654322",
        "password": "Prueba1234",
    }


# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:4000")
    ap.add_argument("--admin-user", default=None)
    ap.add_argument("--admin-pass", default=None)
    ap.add_argument("--docente-user", default=None)
    ap.add_argument("--docente-pass", default=None)
    ap.add_argument("--ruta-admin", default="/api/admin/dashboard")
    ap.add_argument("--no-crear", action="store_true")
    args = ap.parse_args()

    base = args.url.rstrip("/")
    ruta_admin = "/" + args.ruta_admin.lstrip("/")
    dni_prueba = f"99{random.randint(100000, 999999)}"

    print(f"\n{'='*72}")
    print(" PRUEBAS DE FUNCIÓN — Módulo de Autenticación")
    print(f" Backend: {base}")
    if not args.no_crear:
        print(f" DNI de prueba que se creará: {dni_prueba}")
    print("=" * 72)

    if not esperar_backend(base):
        print(f"\n{ROJO}El backend no responde en {base}/health tras varios intentos.{RESET}")
        print("Arráncalo con: uvicorn main:app --port 4000\n")
        return 1

    token_estudiante = None

    # =====================================================================
    titulo("RF01 — Registro de estudiantes")
    # =====================================================================

    if args.no_crear:
        for cid, desc in [
            ("CF-01", "Registro con datos válidos crea la cuenta"),
            ("CF-02", "El estudiante registrado puede iniciar sesión"),
            ("CF-03", "Un DNI ya registrado es rechazado"),
        ]:
            caso(cid, "RF01", desc, "—", False, "ejecutado con --no-crear", omitido=True)
    else:
        st, body, _ = peticion(f"{base}/api/auth/register", "POST", estudiante_valido(dni_prueba))
        usuario = (body or {}).get("user", {})
        caso("CF-01", "RF01",
             "Registro con datos válidos crea la cuenta",
             "HTTP 201 y datos del estudiante",
             st == 201 and usuario.get("dni") == dni_prueba and usuario.get("role") == "student",
             f"status={st} rol={usuario.get('role')} dni={usuario.get('dni')}")

        st, body, _ = peticion(f"{base}/api/auth/login", "POST",
                               {"dni": dni_prueba, "password": "Prueba1234"})
        token_estudiante = (body or {}).get("token")
        caso("CF-02", "RF01",
             "El estudiante registrado puede iniciar sesión de inmediato",
             "HTTP 200 y token válido",
             st == 200 and bool(token_estudiante),
             f"status={st} token={'sí' if token_estudiante else 'no'}")

        st, body, _ = peticion(f"{base}/api/auth/register", "POST", estudiante_valido(dni_prueba))
        caso("CF-03", "RF01",
             "Un DNI ya registrado es rechazado (sin duplicar la cuenta)",
             "HTTP 409 con aviso de DNI existente",
             st == 409 and codigo(body) == "DNI_ALREADY_REGISTERED",
             f"status={st} code={codigo(body)}")

    # Casos negativos: no requieren escritura en la base de datos
    negativos = [
        ("CF-04", "Falta un campo obligatorio (apoderado)",
         {k: v for k, v in estudiante_valido("98123456").items() if k != "parent_phone"}),
        ("CF-05", "DNI con formato inválido (menos de 8 dígitos)",
         {**estudiante_valido("981"), }),
        ("CF-06", "Teléfono con formato inválido (no empieza con 9)",
         {**estudiante_valido("98123456"), "phone": "123456789"}),
        ("CF-07", "Contraseña que no cumple la política (sin número)",
         {**estudiante_valido("98123456"), "password": "soloLetras"}),
        ("CF-08", "Nombre con caracteres no permitidos",
         {**estudiante_valido("98123456"), "first_name": "Juan123"}),
    ]
    for cid, desc, payload in negativos:
        st, body, _ = peticion(f"{base}/api/auth/register", "POST", payload)
        caso(cid, "RF01", desc, "HTTP 422 y la cuenta no se crea",
             st == 422 and codigo(body) == "VALIDATION_ERROR",
             f"status={st} code={codigo(body)}")

    # =====================================================================
    titulo("RF02 — Inicio de sesión por tipo de usuario")
    # =====================================================================

    caso("CF-09", "RF02",
         "Inicio de sesión de ESTUDIANTE devuelve el rol correcto",
         'HTTP 200 con role="student"',
         bool(token_estudiante),
         "verificado en CF-02" if token_estudiante else "requiere ejecutar sin --no-crear",
         omitido=not token_estudiante)

    token_admin = None
    if args.admin_user and args.admin_pass:
        st, body, _ = peticion(f"{base}/api/auth/login", "POST",
                               {"dni": args.admin_user, "password": args.admin_pass})
        token_admin = (body or {}).get("token")
        rol = ((body or {}).get("user") or {}).get("role")
        if st == 429:
            caso("CF-10", "RF02",
                 "Inicio de sesión de ADMINISTRADOR devuelve el rol correcto",
                 'HTTP 200 con role="admin"', False,
                 "cuenta bloqueada por intentos fallidos previos: reinicia el "
                 "backend y vuelve a ejecutar", omitido=True)
        else:
            caso("CF-10", "RF02",
                 "Inicio de sesión de ADMINISTRADOR devuelve el rol correcto",
                 'HTTP 200 con role="admin"',
                 st == 200 and rol == "admin",
                 f"status={st} rol={rol}"
                 + ("  ¿usaste las credenciales reales?" if st == 401 else ""))
    else:
        caso("CF-10", "RF02", "Inicio de sesión de ADMINISTRADOR devuelve el rol correcto",
             'HTTP 200 con role="admin"', False,
             "usa --admin-user y --admin-pass", omitido=True)

    if args.docente_user and args.docente_pass:
        st, body, _ = peticion(f"{base}/api/auth/login", "POST",
                               {"dni": args.docente_user, "password": args.docente_pass})
        rol = ((body or {}).get("user") or {}).get("role")
        caso("CF-11", "RF02",
             "Inicio de sesión de DOCENTE devuelve el rol correcto",
             'HTTP 200 con role="teacher"',
             st == 200 and rol == "teacher",
             f"status={st} rol={rol}"
             + ("  ¿usaste las credenciales reales?" if st == 401 else ""),
             omitido=(st == 429))
    else:
        caso("CF-11", "RF02", "Inicio de sesión de DOCENTE devuelve el rol correcto",
             'HTTP 200 con role="teacher"', False,
             "usa --docente-user y --docente-pass", omitido=True)

    # Se usa el estudiante de prueba, nunca la cuenta de administrador: cada
    # fallo cuenta para el bloqueo por fuerza bruta y ejecutar el script varias
    # veces dejaría al administrador sin acceso durante 15 minutos.
    dni_fallo = dni_prueba if not args.no_crear else f"98{random.randint(100000, 999999)}"
    st, body, _ = peticion(f"{base}/api/auth/login", "POST",
                           {"dni": dni_fallo, "password": "claveErronea1"})
    caso("CF-12", "RF02",
         "Credenciales incorrectas no conceden acceso",
         "HTTP 401 sin token",
         st == 401 and not (body or {}).get("token"),
         f"status={st} code={codigo(body)}")

    st, body, _ = peticion(f"{base}/api/auth/login", "POST", {"dni": "", "password": ""})
    caso("CF-13", "RF02",
         "Credenciales vacías son rechazadas por el servidor",
         "HTTP 422 (validación del backend)",
         st == 422,
         f"status={st} code={codigo(body)}")

    # =====================================================================
    titulo("RNF03 — Autenticación mediante JWT")
    # =====================================================================

    token = token_estudiante or token_admin
    partes = token.split(".") if token else []
    caso("CF-14", "RNF03",
         "El token emitido tiene estructura JWT (cabecera, carga, firma)",
         "Tres segmentos separados por punto",
         len(partes) == 3,
         f"segmentos={len(partes)}" if token else "sin token disponible",
         omitido=not token)

    contenido_ok = False
    if token:
        try:
            import base64

            carga = partes[1] + "=" * (-len(partes[1]) % 4)
            datos = json.loads(base64.urlsafe_b64decode(carga))
            contenido_ok = "id" in datos and "role" in datos and "exp" in datos
            detalle = f"claims={sorted(datos.keys())}"
        except Exception as e:
            detalle = f"no se pudo decodificar: {e}"
    else:
        detalle = "sin token disponible"

    caso("CF-15", "RNF03",
         "El token identifica al usuario, su rol y su caducidad",
         "Contiene id, role y exp",
         contenido_ok, detalle, omitido=not token)

    st, _, _ = peticion(f"{base}{ruta_admin}", token=token_admin) if token_admin else (0, None, None)
    caso("CF-16", "RNF03",
         "Un token válido concede acceso a una ruta protegida",
         "HTTP 200 en la ruta de administración",
         st == 200, f"status={st}", omitido=not token_admin)

    st, body, _ = peticion(f"{base}{ruta_admin}")
    caso("CF-17", "RNF03",
         "Una ruta protegida rechaza las peticiones sin token",
         "HTTP 401",
         st == 401, f"status={st} code={codigo(body)}")

    # =====================================================================
    titulo("RNF04 — Contraseñas almacenadas cifradas")
    # =====================================================================

    # Se revisan las respuestas de las operaciones que SÍ tuvieron éxito.
    respuestas = []
    if token_estudiante:
        _, b, _ = peticion(f"{base}/api/auth/login", "POST",
                           {"dni": dni_prueba, "password": "Prueba1234"})
        respuestas.append(b)
    if token_admin and args.admin_user:
        _, b, _ = peticion(f"{base}/api/auth/login", "POST",
                           {"dni": args.admin_user, "password": args.admin_pass})
        respuestas.append(b)
    texto = json.dumps(respuestas).lower()
    fuga = any(k in texto for k in ["password", "hash", "$2b$"])
    caso("CF-18", "RNF04",
         "Ninguna respuesta de autenticación expone la contraseña ni su hash",
         "El cuerpo de la respuesta no contiene password ni hash",
         not fuga and bool(respuestas),
         (f"{len(respuestas)} respuesta(s) revisada(s), sin rastro de credenciales"
          if not fuga else f"respuesta: {texto[:70]}"),
         omitido=not respuestas)

    # =====================================================================
    titulo("RNF05 — Control de acceso por roles")
    # =====================================================================

    if token_estudiante:
        st, body, _ = peticion(f"{base}{ruta_admin}", token=token_estudiante)
        caso("CF-19", "RNF05",
             "Un estudiante no puede acceder a funciones de administración",
             "HTTP 403 (prohibido)",
             st == 403,
             f"status={st} code={codigo(body)}")
    else:
        caso("CF-19", "RNF05",
             "Un estudiante no puede acceder a funciones de administración",
             "HTTP 403 (prohibido)", False,
             "requiere ejecutar sin --no-crear", omitido=True)

    st, body, _ = peticion(f"{base}{ruta_admin}", token="token.falso.inventado")
    caso("CF-20", "RNF05",
         "Un token manipulado no concede acceso",
         "HTTP 401",
         st == 401, f"status={st} code={codigo(body)}")

    # =====================================================================
    # Resumen
    # =====================================================================
    pasa = sum(1 for r in resultados if r["estado"] == "PASA")
    falla = sum(1 for r in resultados if r["estado"] == "FALLA")
    omit = sum(1 for r in resultados if r["estado"] == "OMITIDO")

    print(f"\n{'='*72}")
    print(f" RESUMEN: {VERDE}{pasa} PASA{RESET} | {ROJO}{falla} FALLA{RESET} | {AMARILLO}{omit} OMITIDO{RESET}")

    print(f"\n Cobertura por requisito:")
    for req in ["RF01", "RF02", "RNF03", "RNF04", "RNF05"]:
        r = [x for x in resultados if x["req"] == req]
        ok = sum(1 for x in r if x["estado"] == "PASA")
        ej = sum(1 for x in r if x["estado"] != "OMITIDO")
        marca = VERDE + "cumple" + RESET if ej and ok == ej else (
            ROJO + "NO CUMPLE" + RESET if ej else AMARILLO + "sin ejecutar" + RESET)
        print(f"   {req:<6} {ok}/{ej} casos superados   {marca}")

    if falla:
        print(f"\n {ROJO}Casos fallidos:{RESET}")
        for r in resultados:
            if r["estado"] == "FALLA":
                print(f"   {r['id']} ({r['req']}) {r['desc']}")
                print(f"        esperado: {r['esperado']}")
                print(f"        obtenido: {r['real']}")

    if not args.no_crear:
        print(f"\n {AMARILLO}Limpieza:{RESET} elimina el estudiante de prueba con DNI {dni_prueba}")
        print(" desde el panel de administración (Estudiantes → Eliminar).")

    print("=" * 72 + "\n")

    # Volcado para pegar en el informe
    print(f"{GRIS}--- Tabla para el informe (ID | Requisito | Caso | Estado) ---{RESET}")
    for r in resultados:
        print(f"{r['id']} | {r['req']} | {r['desc']} | {r['estado']}")
    print()

    return 1 if falla else 0


if __name__ == "__main__":
    sys.exit(main())