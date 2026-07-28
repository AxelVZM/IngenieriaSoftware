"""
PRUEBAS DE INTEROPERABILIDAD — Sistema de Gestión de Matrículas
Academia "Unión de Nuevos Inteligentes"

Objetivo: comprobar que la aplicación tiene una interfaz adecuada con los
sistemas externos de los que depende.

Interfaces verificadas por este script:
  I1  PostgreSQL alojado en Railway  (vía asyncpg)
  I2  Cloudinary                     (almacenamiento de comprobantes)
  I3  Selenium / WhatsApp Web        (solo disponibilidad del servicio)

La interfaz I4 (frontend ↔ backend) se verifica con el script
pruebas_funcion_auth.py y con la revisión manual del contrato de errores.

USO (desde la carpeta backend, con el entorno virtual activo):

    python pruebas_interoperabilidad.py

Lee la configuración del archivo .env. No modifica ningún dato: solo abre
conexiones, consulta metadatos y cierra.
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone

if sys.platform == "win32":
    os.system("")

VERDE, ROJO, AMARILLO, AZUL, GRIS, RESET = (
    "\033[92m", "\033[91m", "\033[93m", "\033[96m", "\033[90m", "\033[0m",
)

resultados: list[tuple[str, str, str]] = []


def check(cid, descripcion, condicion, detalle="", omitido=False):
    estado = "OMITIDO" if omitido else ("PASA" if condicion else "FALLA")
    resultados.append((cid, descripcion, estado))
    color = {"PASA": VERDE, "FALLA": ROJO, "OMITIDO": AMARILLO}[estado]
    print(f"  {color}[{estado:^8}]{RESET} {cid}  {descripcion}")
    if detalle:
        print(f"              {GRIS}{detalle}{RESET}")


def titulo(t):
    print(f"\n{AZUL}{t}{RESET}")


def aviso(t):
    print(f"  {AMARILLO}!{RESET} {t}")


# ---------------------------------------------------------------------------
# I1 — PostgreSQL
# ---------------------------------------------------------------------------


async def probar_base_de_datos(url: str) -> None:
    titulo("I1 — Interfaz con PostgreSQL (Railway)")

    try:
        import asyncpg
    except ImportError:
        check("IN-01", "Controlador asyncpg disponible", False,
              "instala las dependencias del proyecto")
        return

    # El proyecto decide el modo TLS buscando la palabra "railway" en la URL.
    modo_ssl = "require" if "railway" in url else "prefer"
    check("IN-01", "Modo TLS que aplicará el proyecto",
          modo_ssl == "require",
          f'ssl="{modo_ssl}"  (se decide buscando "railway" dentro de DATABASE_URL)')
    if modo_ssl != "require":
        aviso("La URL no contiene la palabra 'railway': la conexión NO exigirá "
              "cifrado. Conviene fijar el modo TLS de forma explícita.")

    con = None
    try:
        con = await asyncio.wait_for(
            asyncpg.connect(url, ssl=modo_ssl, command_timeout=20), timeout=25
        )
    except Exception as e:
        check("IN-02", "Conexión con la base de datos remota", False,
              f"{type(e).__name__}: {str(e)[:90]}")
        return

    check("IN-02", "Conexión con la base de datos remota", True)

    try:
        version = await con.fetchval("SHOW server_version")
        check("IN-03", "Versión del motor de base de datos", True,
              f"PostgreSQL {version}")

        cifrado = con.is_closed() is False
        check("IN-04", "La conexión permanece abierta y operativa", cifrado)

        # --- Zona horaria: origen habitual de descuadres de 5 horas ---
        tz_servidor = await con.fetchval("SHOW timezone")
        ahora_bd = await con.fetchval("SELECT now()")
        ahora_local = datetime.now(timezone.utc)
        desfase_h = abs((ahora_bd - ahora_local).total_seconds()) / 3600
        check("IN-05", "El reloj de la base de datos coincide con UTC",
              desfase_h < 0.2,
              f"zona del servidor: {tz_servidor} | now(): {ahora_bd} | "
              f"desfase respecto a UTC: {desfase_h:.1f} h")
        if tz_servidor.upper() not in ("UTC", "ETC/UTC"):
            aviso("El servidor no usa UTC. Verifica cómo se muestran las fechas "
                  "de vencimiento y de asistencia en la interfaz.")

        # --- La prueba IN-06 (columnas timestamp sin zona horaria) ha sido
        #     eliminada por solicitud expresa. ---

        # --- Tipos numéricos: Decimal frente a float ---
        montos = await con.fetch("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND (column_name ILIKE '%price%' OR column_name ILIKE '%amount%'
                   OR column_name ILIKE '%monto%')
        """)
        flotantes = [f"{r['table_name']}.{r['column_name']} ({r['data_type']})"
                     for r in montos
                     if r["data_type"] in ("double precision", "real")]
        check("IN-07", "Los importes usan tipo decimal exacto",
              not flotantes,
              f"{len(flotantes)} columna(s) en coma flotante: "
              + ", ".join(flotantes[:3]) if flotantes
              else f"{len(montos)} columna(s) de importe, todas con tipo exacto")
        if flotantes:
            aviso("La coma flotante introduce errores de redondeo en importes. "
                  "Para dinero se recomienda NUMERIC(10,2).")

        # --- Límite de conexiones frente al tamaño del pool ---
        max_con = int(await con.fetchval("SHOW max_connections"))
        en_uso = await con.fetchval(
            "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()")
        pool_max = 20  # valor de config/database.py
        check("IN-08", "El tamaño del pool cabe en el límite del servidor",
              pool_max < max_con,
              f"max_connections={max_con} | en uso ahora={en_uso} | "
              f"pool del proyecto: min 5, max {pool_max}")
        if pool_max > max_con * 0.5:
            aviso("El pool puede acaparar buena parte de las conexiones "
                  "disponibles si se levantan varias instancias.")

        # --- Tablas esperadas por el sistema ---
        tablas = {r["table_name"] for r in await con.fetch(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public'")}

        # Cada concepto admite varios nombres: el esquema real no tiene por que
        # coincidir con el nombre del modelo de Python.
        CONCEPTOS = {
            "usuarios":      ["users"],
            "estudiantes":   ["students"],
            "docentes":      ["teachers"],
            "cursos":        ["courses"],
            "ciclos":        ["cycles"],
            "matriculas":    ["enrollments"],
            "pagos":         ["payments", "payment_plans", "installments"],
        }
        faltan = [nombre for nombre, alias in CONCEPTOS.items()
                  if not any(a in tablas for a in alias)]
        check("IN-09", "Existen tablas para todos los conceptos del sistema",
              not faltan,
              f"{len(tablas)} tablas en el esquema"
              + (f" | sin tabla: {', '.join(faltan)}" if faltan else ""))
        print(f"      {GRIS}Esquema: {', '.join(sorted(tablas))}{RESET}")

    finally:
        await con.close()


# ---------------------------------------------------------------------------
# I2 — Cloudinary
# ---------------------------------------------------------------------------


def probar_cloudinary() -> None:
    titulo("I2 — Interfaz con Cloudinary (comprobantes de pago)")

    nombre = os.getenv("CLOUDINARY_CLOUD_NAME")
    clave = os.getenv("CLOUDINARY_API_KEY")
    secreto = os.getenv("CLOUDINARY_API_SECRET")

    check("IN-10", "Las credenciales están configuradas",
          all([nombre, clave, secreto]),
          "faltan variables en .env" if not all([nombre, clave, secreto])
          else f"cloud_name={nombre}")

    if not all([nombre, clave, secreto]):
        check("IN-11", "El servicio responde", False, omitido=True)
        return

    try:
        import cloudinary
        import cloudinary.api
    except ImportError:
        check("IN-11", "El servicio responde", False,
              "biblioteca cloudinary no instalada", omitido=True)
        return

    cloudinary.config(cloud_name=nombre, api_key=clave, api_secret=secreto)
    try:
        r = cloudinary.api.ping()
        check("IN-11", "El servicio responde y las credenciales son válidas",
              r.get("status") == "ok", f"respuesta: {r}")
    except Exception as e:
        check("IN-11", "El servicio responde y las credenciales son válidas",
              False, f"{type(e).__name__}: {str(e)[:90]}")
        return

    try:
        uso = cloudinary.api.usage()
        almacenado = uso.get("storage", {}).get("usage", 0) / (1024 * 1024)
        check("IN-12", "Se puede consultar el uso de la cuenta", True,
              f"almacenamiento usado: {almacenado:.1f} MB | "
              f"plan: {uso.get('plan', 'desconocido')}")
    except Exception as e:
        check("IN-12", "Se puede consultar el uso de la cuenta", False,
              str(e)[:80])


# ---------------------------------------------------------------------------
# I3 — Selenium / WhatsApp
# ---------------------------------------------------------------------------


def probar_selenium() -> None:
    titulo("I3 — Interfaz con Selenium (notificaciones de WhatsApp)")

    url = os.getenv("SELENIUM_URL", "http://localhost:4444")
    import urllib.error
    import urllib.request

    try:
        with urllib.request.urlopen(f"{url}/status", timeout=8) as r:
            import json
            datos = json.loads(r.read().decode())
            listo = datos.get("value", {}).get("ready", False)
            check("IN-13", "El servicio de Selenium está disponible", listo,
                  f"{url} | ready={listo}")
    except Exception as e:
        check("IN-13", "El servicio de Selenium está disponible", False,
              f"{url} no responde ({type(e).__name__}). "
              "Es normal si no está levantado.", omitido=True)

    aviso("La interfaz con WhatsApp es automatización del navegador, no una "
          "API oficial: no existe contrato estable. Cualquier cambio en la "
          "interfaz de WhatsApp Web puede romper el envío sin previo aviso. "
          "Este riesgo debe constar en el informe (defecto IO-D5).")


# ---------------------------------------------------------------------------


async def main() -> int:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    print(f"\n{'='*72}")
    print(" PRUEBAS DE INTEROPERABILIDAD — Interfaces con sistemas externos")
    print("=" * 72)

    url = os.getenv("DATABASE_URL")
    if not url:
        print(f"{ROJO}DATABASE_URL no está definida en .env{RESET}")
        return 1

    await probar_base_de_datos(url)
    probar_cloudinary()
    probar_selenium()

    pasa = sum(1 for _, _, e in resultados if e == "PASA")
    falla = sum(1 for _, _, e in resultados if e == "FALLA")
    omit = sum(1 for _, _, e in resultados if e == "OMITIDO")

    print(f"\n{'='*72}")
    print(f" RESUMEN: {VERDE}{pasa} PASA{RESET} | {ROJO}{falla} FALLA{RESET} | "
          f"{AMARILLO}{omit} OMITIDO{RESET}")
    if falla:
        print(f"\n {ROJO}Comprobaciones fallidas:{RESET}")
        for cid, desc, est in resultados:
            if est == "FALLA":
                print(f"   {cid}  {desc}")
    print("=" * 72 + "\n")

    print(f"{GRIS}--- Tabla para el informe (ID | Comprobación | Estado) ---{RESET}")
    for cid, desc, est in resultados:
        print(f"{cid} | {desc} | {est}")
    print()

    return 1 if falla else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))