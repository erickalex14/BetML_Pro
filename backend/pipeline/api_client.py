import requests
import time
import logging

from urllib3.util import url

from backend.pipeline.config import BASE_URL, HEADERS

#Sistema de logs de python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
log = logging.getLogger(__name__)

"""
Función base para TODAS las llamadas a API-Football.

Parámetros:
  endpoint → el path de la API, ej: "/fixtures"
  params   → diccionario con los query params, ej: {"league": 39}

Retorna:
  El JSON de respuesta como diccionario de Python,
  o un dict vacío si hubo error.
"""

def get(endpoint: str, params: dict = None) -> dict:
    url = f"{BASE_URL}{endpoint}"

    log.info(f"Llamando: {url} | params: {params}")

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=10
        )
        response.raise_for_status()

        data = response.json()

        #Log de error por si acaso, apifootball siempre envia el campo error aunque el status sea 200
        if data.get("errors"):
            log.error(f"Error de API: {data['errors']}")
            return {}

        log.info(f"Respuesta OK - {data.get('results', 0)} resultados")
        return data

    except requests.exceptions.Timeout:
        log.error(f"Timeout Error - {endpoint}")
        return {}

    except requests.exceptions.HTTPError as e:
        log.error(f"HTTP Error: {e.response.status_code} — {e}")
        return {}

    except requests.exceptions.RequestException as e:
        log.error(f"Error de conexión: {e}")
        return {}


"""
    trae todos los partidos de una liga especifica
      Parámetros:
      liga_id   → ID de la liga (ej: 39 para Premier League)
      temporada → año de la temporada (ej: 2024)

    Retorna:
      Lista de partidos. Cada partido es un diccionario
      con toda la info: equipos, hora, estado, etc.
"""

def get_fixtures_hoy(liga_id: int, temporada: int) -> list:
    data = get("/fixtures", params={
        "league": liga_id,
        "season": temporada,
        "date": _fecha_hoy()
    })
    return data.get("response", [])


"""
    Trae la tabla de posiciones de una liga,
    feature del modelo de ML: La posicion de un equipo afecta la motivacion del equipo
"""

def get_standings(liga_id: int, temporada: int) -> list:
    data = get("/standings", params={
        "league": liga_id,
        "season": temporada,
    })
    return data.get("response", [])

"""
    Trae estadísticas detalladas de un equipo en una liga:
    goles, tiros, corners, tarjetas, forma reciente, etc.
    Estas son las features principales del modelo ML.
"""

def get_estadisticas_equipo(equipo_id, liga_id: int, temporada: int) -> dict:
    data = get("/team/statistics", params={
        "team": equipo_id,
        "league": liga_id,
        "season": temporada,
    })
    return data.get("response", {})

"""
    Trae el historial de enfrentamientos directos (H2H)
    entre dos equipos — los últimos 10 partidos entre ellos.
    Feature muy importante para el modelo.
"""

def get_h2h(equipo_local_id: int, equipo_visitante_id: int) -> list:
    data = get("/fixtures/headtohead", params={
        "h2h": f"{equipo_local_id}-{equipo_visitante_id}",
        "last": 10
    })
    return data.get("response", [])

#Metodo auxiliar para obtener fecha de hoy
def _fecha_hoy():
    from datetime import date
    return date.today().isoformat()
