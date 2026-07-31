import os
from pathlib import Path

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
}

