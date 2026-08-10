"""
Verificacion de las correcciones del modulo de autenticacion.

Ejecuta pruebas contra el backend EN EJECUCION y reporta PASA / FALLA por
cada hallazgo de la revision. Sirve como evidencia para el informe.

USO (con el backend corriendo en otra terminal):

    python verificar_correcciones.py
    python verificar_correcciones.py --url http://127.0.0.1:4000 --dni 12345678

Parametros:
    --url   URL base del backend (por defecto http://127.0.0.1:4000)
    --ruta  Un endpoint protegido de tu API (por defecto /api/admin/dashboard).
    --dni   Un DNI que SI exista en tu base de datos. Se usa para comprobar
            que el sistema responde igual ante un DNI real con contrasena
            incorrecta y ante un DNI inexistente. Sin este parametro esa
            prueba se omite.

AVISO: la prueba de fuerza bruta deja bloqueado el DNI 00000000 desde esta
IP durante ~15 minutos. Es un DNI ficticio, no afecta a usuarios reales.

No requiere librerias externas: usa solo la libreria estandar.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import urllib.error
import urllib.request

if sys.platform == "win32":
    import os

    os.system("")  # habilita los codigos ANSI en la consola de Windows

VERDE, ROJO, AMARILLO, GRIS, RESET = (
    "\033[92m",
    "\033[91m",
    "\033[93m",
    "\033[90m",
    "\033[0m",
)

resultados: list[tuple[str, str]] = []


def peticion(url: str, metodo: str = "GET", cuerpo=None, token=None, timeout=10):
    """Devuelve (status, body_dict, headers). Nunca lanza por status HTTP."""
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(url, data=datos, method=metodo)
    req.add_header("Content-Type", "application/json")
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
        print(f"{ROJO}No se pudo conectar con {url}: {e.reason}{RESET}")
        print("Verifica que el backend este corriendo (uvicorn main:app --port 4000)")
        sys.exit(1)


def codigo(body) -> str:
    d = (body or {}).get("detail")
    return d.get("code", "") if isinstance(d, dict) else ""


def mensaje(body) -> str:
    d = (body or {}).get("detail")
    return d.get("message", "") if isinstance(d, dict) else str(d)


def check(nombre: str, condicion: bool, detalle: str = "", omitido: bool = False):
    if omitido:
        resultados.append((nombre, "OMITIDO"))
        print(f"  {AMARILLO}[ OMITIDO ]{RESET} {nombre}")
    elif condicion:
        resultados.append((nombre, "PASA"))
        print(f"  {VERDE}[  PASA   ]{RESET} {nombre}")
    else:
        resultados.append((nombre, "FALLA"))
        print(f"  {ROJO}[  FALLA  ]{RESET} {nombre}")
    if detalle:
        print(f"             {GRIS}{detalle}{RESET}")


# ---------------------------------------------------------------------------


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://127.0.0.1:4000")
    p.add_argument("--dni", default=None, help="DNI existente en tu BD")
    p.add_argument(
        "--ruta",
        default="/api/admin/dashboard",
        help="Un endpoint protegido de tu API para probar la validacion de token",
    )
    args = p.parse_args()
    base = args.url.rstrip("/")
    ruta_prot = "/" + args.ruta.lstrip("/")

    print(f"\n{'='*70}\n VERIFICACION DE CORRECCIONES - Modulo de autenticacion")
    print(f" Backend: {base}\n{'='*70}")

    # --- 1. Validacion en el backend -------------------------------------
    print("\n[1] Validacion de datos en el backend (ya no depende del frontend)")

    st, body, _ = peticion(
        f"{base}/api/auth/register",
        "POST",
        {
            "dni": "123",
            "first_name": "Juan",
            "last_name": "Perez",
            "phone": "987654321",
            "parent_name": "Maria",
            "parent_phone": "987654321",
            "password": "clave1234",
        },
    )
    check("DNI invalido rechazado con 422", st == 422, f"status={st} code={codigo(body)}")
    check("Codigo VALIDATION_ERROR presente", codigo(body) == "VALIDATION_ERROR")

    st, body, _ = peticion(
        f"{base}/api/auth/register",
        "POST",
        {
            "dni": "87654321",
            "first_name": "Juan",
            "last_name": "Perez",
            "phone": "987654321",
            "parent_name": "Maria",
            "parent_phone": "987654321",
            "password": "soloLetras",
        },
    )
    check("Contrasena sin numero rechazada", st == 422, f"mensaje: {mensaje(body)[:60]}")

    st, body, _ = peticion(
        f"{base}/api/auth/register",
        "POST",
        {
            "dni": "87654321",
            "first_name": "Juan9",
            "last_name": "Perez",
            "phone": "123456789",
            "parent_name": "Maria",
            "parent_phone": "987654321",
            "password": "clave1234",
        },
    )
    check("Nombre con digitos y telefono invalido rechazados", st == 422)

    # --- 2. Enumeracion de usuarios --------------------------------------
    print("\n[2] Enumeracion de usuarios (no se revela si el DNI existe)")

    # Cada DNI inexistente es distinto para no activar el bloqueo por
    # intentos fallidos (la clave del contador es DNI + IP).
    contador_falsos = [0]

    def login_inexistente():
        contador_falsos[0] += 1
        return peticion(
            f"{base}/api/auth/login",
            "POST",
            {"dni": f"99{contador_falsos[0]:06d}", "password": "loQueSea1"},
        )

    def login_real():
        return peticion(
            f"{base}/api/auth/login",
            "POST",
            {"dni": args.dni, "password": "contrasenaIncorrecta1"},
        )

    # CALENTAMIENTO: la primera peticion paga el handshake TLS con la base de
    # datos, la creacion del pool y la carga de bcrypt. Medir sin calentar da
    # diferencias de segundos que no tienen nada que ver con seguridad.
    print(f"    {GRIS}calentando conexiones...{RESET}")
    for _ in range(3):
        login_inexistente()

    st_falso, body_falso, _ = login_inexistente()

    if args.dni:
        st_real, body_real, _ = login_real()

        check(
            "Mismo status HTTP para DNI inexistente y DNI real",
            st_falso == st_real == 401,
            f"inexistente={st_falso}  real={st_real}",
        )
        check(
            "Mismo codigo de error",
            codigo(body_falso) == codigo(body_real) == "INVALID_CREDENTIALS",
        )
        check(
            "Mismo mensaje exacto",
            mensaje(body_falso) == mensaje(body_real),
            f'"{mensaje(body_falso)}"',
        )

        # --- Medicion de tiempos -----------------------------------------
        # Se alternan las peticiones para que cualquier lentitud pasajera de
        # la red afecte por igual a ambos casos, y se usa la MEDIANA para
        # descartar picos aislados.
        MUESTRAS = 3  # ojo: cada una gasta un intento del DNI real (max. 5)
        t_falsos, t_reales = [], []
        for _ in range(MUESTRAS):
            t0 = time.perf_counter()
            login_inexistente()
            t_falsos.append(time.perf_counter() - t0)

            t0 = time.perf_counter()
            login_real()
            t_reales.append(time.perf_counter() - t0)

        med_falso = statistics.median(t_falsos)
        med_real = statistics.median(t_reales)
        dif = abs(med_falso - med_real)

        # El umbral se calibra con el costo real de un bcrypt en esta maquina.
        # Una fuga autentica (saltarse el bcrypt cuando el DNI no existe) se
        # nota como una diferencia del orden de UNA operacion bcrypt completa.
        costo_bcrypt = 0.25
        try:
            from utils.security import get_password_hash, verify_password

            h = get_password_hash("medicion1234")
            t0 = time.perf_counter()
            verify_password("medicion1234", h)
            costo_bcrypt = time.perf_counter() - t0
        except Exception:
            pass

        umbral = max(0.20, costo_bcrypt * 0.6)
        muestras_txt = (
            "inexistente=["
            + ", ".join(f"{t*1000:.0f}" for t in t_falsos)
            + "]  real=["
            + ", ".join(f"{t*1000:.0f}" for t in t_reales)
            + "] ms"
        )
        check(
            "Tiempos de respuesta similares (sin timing attack)",
            dif < umbral,
            f"medianas: {med_falso*1000:.0f}ms vs {med_real*1000:.0f}ms  "
            f"dif={dif*1000:.0f}ms  umbral={umbral*1000:.0f}ms "
            f"(1 bcrypt={costo_bcrypt*1000:.0f}ms)",
        )
        print(f"             {GRIS}{muestras_txt}{RESET}")
        print(
            f"             {GRIS}Nota: el DNI {args.dni} queda con {MUESTRAS + 1} intentos "
            f"fallidos. Reinicia el backend para limpiarlos.{RESET}"
        )
    else:
        check("Comparacion con DNI real", False, omitido=True)
        print(f"             {GRIS}Ejecuta con --dni <un DNI real de tu BD>{RESET}")
        check(
            "DNI inexistente devuelve 401 generico",
            st_falso == 401 and codigo(body_falso) == "INVALID_CREDENTIALS",
            f'"{mensaje(body_falso)}"',
        )

    palabras_delatoras = ["no se encontr", "no existe", "registrate", "regístrate", "verifica el n"]
    texto = mensaje(body_falso).lower()
    check(
        "El mensaje no delata que el DNI no existe",
        not any(w in texto for w in palabras_delatoras),
    )

    # --- 3. Control de intentos fallidos ---------------------------------
    print("\n[3] Control de intentos fallidos (fuerza bruta)")

    dni_prueba = "00000000"
    bloqueado_en = None
    retry_after = None
    for intento in range(1, 9):
        st, body, headers = peticion(
            f"{base}/api/auth/login",
            "POST",
            {"dni": dni_prueba, "password": f"intento{intento}"},
        )
        if st == 429:
            bloqueado_en = intento
            retry_after = headers.get("Retry-After") or headers.get("retry-after")
            break

    check(
        "El login se bloquea tras varios intentos fallidos",
        bloqueado_en is not None,
        f"bloqueado en el intento #{bloqueado_en}" if bloqueado_en else "nunca bloqueo tras 8 intentos",
    )
    if bloqueado_en:
        check("Codigo TOO_MANY_ATTEMPTS", codigo(body) == "TOO_MANY_ATTEMPTS")
        check("Cabecera Retry-After presente", retry_after is not None, f"Retry-After={retry_after}")

    # --- 4. Proteccion de rutas y tokens ---------------------------------
    print("\n[4] Validacion de tokens en rutas protegidas")

    st, body, _ = peticion(f"{base}{ruta_prot}")
    ruta_ok = st != 404
    if not ruta_ok:
        print(f"             {GRIS}La ruta no existe. Usa --ruta /api/tu/endpoint/protegido{RESET}")

    check(
        "Sin cabecera Authorization -> 401",
        st == 401 and codigo(body) in ("TOKEN_MISSING", "HTTP_ERROR"),
        f"status={st} code={codigo(body)}",
        omitido=not ruta_ok,
    )

    st, body, _ = peticion(f"{base}{ruta_prot}", token="esto.no.es.un.token")
    check(
        "Token basura -> 401 TOKEN_INVALID",
        st == 401 and codigo(body) == "TOKEN_INVALID",
        f"status={st} code={codigo(body)}",
        omitido=not ruta_ok,
    )

    # Token expirado: se firma localmente con la clave real del proyecto
    token_expirado = None
    try:
        from datetime import timedelta

        from utils.security import create_access_token

        token_expirado = create_access_token(
            {"id": 1, "role": "student"}, expires_delta=timedelta(seconds=-60)
        )
    except Exception as e:
        print(f"             {GRIS}No se pudo firmar un token expirado: {e}{RESET}")

    if token_expirado:
        st, body, _ = peticion(f"{base}{ruta_prot}", token=token_expirado)
        check(
            "Token expirado -> 401 TOKEN_EXPIRED",
            st == 401 and codigo(body) == "TOKEN_EXPIRED",
            f"status={st} code={codigo(body)}",
            omitido=not ruta_ok,
        )
    else:
        check("Token expirado -> 401 TOKEN_EXPIRED", False, omitido=True)
        print(f"             {GRIS}Ejecuta el script desde la carpeta backend/{RESET}")

    # Token con firma de otra clave (falsificado)
    try:
        from jose import jwt

        falso = jwt.encode({"id": 1, "role": "admin"}, "clave-inventada-de-atacante", algorithm="HS256")
        st, body, _ = peticion(f"{base}{ruta_prot}", token=falso)
        check(
            "Token firmado con otra clave -> rechazado",
            st == 401,
            f"status={st} code={codigo(body)}",
            omitido=not ruta_ok,
        )
    except Exception:
        check("Token firmado con otra clave -> rechazado", False, omitido=True)

    # --- 5. Formato estandar de errores ----------------------------------
    print("\n[5] Formato estandar de respuestas de error")

    casos_formato = [
        ("422 validacion", f"{base}/api/auth/register", "POST", {"dni": "1"}),
        ("401 credenciales", f"{base}/api/auth/login", "POST", {"dni": "11111111", "password": "x1"}),
    ]
    if ruta_ok:
        casos_formato.append(("401 sin token", f"{base}{ruta_prot}", "GET", None))

    formatos_ok = True
    for descripcion, url, met, cuerpo in casos_formato:
        st, body, _ = peticion(url, met, cuerpo)
        d = (body or {}).get("detail")
        bien = isinstance(d, dict) and "code" in d and "message" in d
        if not bien:
            formatos_ok = False
            print(f"             {GRIS}{descripcion}: {json.dumps(body)[:80]}{RESET}")

    check("Todos los errores usan {detail:{code,message}}", formatos_ok)

    # --- 6. No se filtra informacion interna -----------------------------
    print("\n[6] Manejo global de excepciones (sin fuga de informacion)")

    st, body, _ = peticion(f"{base}/api/boom")
    if st == 404:
        check("Error 500 no expone stacktrace", False, omitido=True)
        print(f"             {GRIS}Endpoint /api/boom no existe (normal en produccion){RESET}")
    else:
        crudo = json.dumps(body).lower()
        filtra = any(w in crudo for w in ["traceback", "line ", ".py", "valueerror", "password="])
        check("Error 500 no expone stacktrace ni datos internos", st == 500 and not filtra,
              f"status={st} respuesta={json.dumps(body)[:70]}")

    # --- Resumen ---------------------------------------------------------
    pasa = sum(1 for _, r in resultados if r == "PASA")
    falla = sum(1 for _, r in resultados if r == "FALLA")
    omit = sum(1 for _, r in resultados if r == "OMITIDO")

    print(f"\n{'='*70}")
    print(f" RESUMEN: {VERDE}{pasa} PASA{RESET}  |  {ROJO}{falla} FALLA{RESET}  |  {AMARILLO}{omit} OMITIDO{RESET}")
    if falla:
        print("\n Pruebas fallidas:")
        for nombre, r in resultados:
            if r == "FALLA":
                print(f"   - {nombre}")
    print(f"{'='*70}\n")
    return 1 if falla else 0


if __name__ == "__main__":
    sys.exit(main())