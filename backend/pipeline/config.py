import os
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

#Cargamos todo dede el .env

ROOT_DIR = Path(__file__).parent.parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")
API_KEY = os.getenv("API_FOOTBALL_KEY", "")
BASE_URL = os.getenv("API_FOOTBALL_BASE_URL", "https://v3.football.api-sports.io")
DB_URL = os.getenv("DB_URL", "sqlite:///data/betml.db")

#Header para las peticiones de api football
HEADERS = {
    "x-apisports-key": API_KEY
}

_TZ_PARTIDOS = ZoneInfo("America/Guayaquil")


def ahora_partidos() -> datetime:
    """"Ahora" en la misma referencia que Partido.fecha, para poder
    compararlos.

    **Partido.fecha está en UTC**, aunque pipeline_dia.py pida los
    fixtures con timezone=America/Guayaquil. Medido el 2026-08-13 contra
    los startTimestamp de Sofascore en 8 partidos anclados: los 8 dieron
    exactamente 0.0 h de diferencia contra UTC. El síntoma que lo
    delató: la app mostraba el partido de Pafos a las 17:00 cuando en
    Ecuador se jugaba 12:00.

    Antes esta función devolvía hora de Guayaquil dando por sentado lo
    contrario, así que todas las comparaciones contra fecha estaban
    corridas 5 horas: la detección de "ya debería haber arrancado", la
    ventana de 90 min de las alineaciones y los límites del día.

    Ojo: NO usar para mostrarle horas al usuario. Para eso el backend
    manda la fecha marcada como UTC y el celular la pasa a su hora
    local (ver PartidoService._enriquecer)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

#ID'S DE LAS LIGAS

LIGAS = {
"Premier League":          39,
    "La Liga":             140,
    "Serie A":             135,
    "Bundesliga":          78,
    "Ligue 1":             61,
    "Champions League":    2,
    "Europa League":       3,
    "Conference League":   848,
    "Copa Libertadores":   13,
    "Copa Sudamericana":   11,
    "Liga MX":             262,
    "MLS":                 253,
    "Brasileirao":         71,
    "Liga Argentina":      128,
    "LigaPro Ecuador":     242,
    "Eredivisie":          88,
    "Saudi Pro League":    307,
    "UEFA Super Cup":      531,
    "Friendlies":          10,   # amistosos de selecciones
    "Friendlies Clubs":    667,  # amistosos de pretemporada de clubes
}

# Amistosos: se guardan y se pueden predecir, pero NO cuentan como
# historial para calcular forma/win-rate/H2H de NINGÚN equipo — suplentes
# y bajo ritmo real en pretemporada/fecha FIFA ensuciarían la forma que
# se usa para predecir partidos oficiales. Ver features/calculador.py y
# features/jugadores.py, todas las queries de historial excluyen estos ids.
LIGAS_SIN_HISTORIAL_ID = {10, 667}

# Torneos puntuales (no recurrentes) — fuera de LIGAS a propósito:
# ese dict lo iteran también job_temporada_actual.py y pipeline_dia.py,
# jobs de "temporada en curso" que correrían para siempre contra un
# torneo que ya terminó.
TORNEOS_PUNTUALES = {
    "World Cup": (1, 2026),  # (liga_id API-Football, temporada)
}

# Temporada actual por liga — varía según competición
TEMPORADA_ACTUAL = {
    "Premier League":    2025,
    "La Liga":           2025,
    "Serie A":           2025,
    "Bundesliga":        2025,
    "Ligue 1":           2025,
    "Champions League":  2025,
    "Europa League":     2025,
    "Conference League": 2025,
    "Copa Libertadores": 2026,
    "Copa Sudamericana": 2026,
    "Liga MX":           2025,
    "MLS":               2025,
    "Brasileirao":       2025,
    "Liga Argentina":    2025,
    "LigaPro Ecuador":   2025,
    "Eredivisie":        2025,
    "Saudi Pro League":  2025,
    "UEFA Super Cup":    2025,
    "Friendlies":        2025,
    "Friendlies Clubs":  2025,
}

