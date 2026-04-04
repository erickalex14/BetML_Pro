import logging
from  backend.pipeline.config import LIGAS
from  backend.pipeline import api_client
from backend.pipeline.guardador import guardar_partido
from backend.db.database import crear_tablas, SessionLocal

log = logging.getLogger(__name__)

TEMPORADA = 2024

def correr_pipeline():
    """
    Pipeline completo del día:
    1. Crea las tablas si no existen
    2. Para cada liga, trae los partidos de hoy
    3. Guarda cada partido en la BD
    """
    log.info("=" * 50)
    log.info("Iniciando Pipeline diario de BetML Pro")
    log.info("=" * 50)

    #Crea las tablas si es la primera vez
    crear_tablas()
    log.info("Tablas creadas/Ok")

    total_guardados = 0

    #Abre sesion en la BD para la ejecuion
    db = SessionLocal()

    try:
        for nombre_liga, liga_id in LIGAS.items():
            log.info(f"Procesando: {nombre_liga}")

            partidos = api_client.get_fixtures_hoy(liga_id, TEMPORADA)
            if not partidos:
                log.info(f"No hay partidos hoy en : {nombre_liga}")
                continue
            for fixture in partidos:
                guardar_partido(db, fixture, liga_id, TEMPORADA)
                total_guardados += 1
        log.info(f"Pipeline completado — {total_guardados} partidos guardados")

    except Exception as e:
        log.error(f"Error en pipeline: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    correr_pipeline()




