import os
from pathlib import Path

from dotenv import load_dotenv

#Cargamos todo dede el .env

ROOT_DIR = Path(__file__).parent.parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")
API_KEY = os.getenv("API_FOOTBALL_KEY", "")
print(f"[DEBUG] ROOT_DIR: {ROOT_DIR}")
print(f"[DEBUG] .env existe: {(ROOT_DIR / '.env').exists()}")
print(f"[DEBUG] Key cargada: {API_KEY[:8]}..." if API_KEY else "[DEBUG] Key: VACÍA")

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
    "LigaPro Ecuador":     314,
    "Eredivisie":          88,
    "Saudi Pro League":    307,
}



