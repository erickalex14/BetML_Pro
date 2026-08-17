from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    #API FOOTBALL
    api_football_key:       str = ""
    api_football_base_url:  str = "https://v3.football.api-sports.io"

    #BASE DE DATOS
    db_url: str = "sqlite:///data/betml.db"

    #APP
    app_name:   str = "BetML Pro"
    app_version: str = "1.0.0"
    debug: bool = False

    #ML
    model_name:        str = "modelo_v1.pkl"
    umbral_confianza:  float = 0.60

    #CUOTAS — fuentes gratis además de Sofascore (ver
    # backend/pipeline/odds/orquestador.py). Vacías = esa fuente se
    # saltea sola, no rompe nada. Van declaradas acá porque Settings
    # rechaza claves del .env que no conozca.
    the_odds_api_key:      str = ""
    odds_api_io_key:       str = ""

    #AUTH — JWT_SECRET_KEY debe venir del .env en producción (nunca el
    # default de acá, es público en el repo). Generar con:
    # python -c "import secrets; print(secrets.token_hex(32))"
    jwt_secret_key:        str = "dev-secret-cambiar-en-produccion"
    jwt_algoritmo:          str = "HS256"
    jwt_expira_minutos:     int = 15
    jwt_refresh_dias:       int = 30
    google_client_id:       str = ""

    class Config:
        #Lee el .env
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
