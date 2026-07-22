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

    class Config:
        #Lee el .env
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()