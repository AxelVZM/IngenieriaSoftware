import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar la aplicación arrastra el middleware de autenticación, que aborta si
# no encuentra un JWT_SECRET. Cuando no está definido, la recolección de pytest
# falla y NINGUNA prueba llega a ejecutarse.
#
# Se carga primero el .env y solo después se pone un valor de relleno, porque
# `setdefault` no pisa lo ya definido: si se hiciera al revés, las pruebas
# usarían el relleno e ignorarían en silencio la clave real del proyecto.
from dotenv import load_dotenv  # noqa: E402

load_dotenv()
os.environ.setdefault("JWT_SECRET", "clave-de-relleno-solo-para-pruebas")
