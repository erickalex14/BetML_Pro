import schedule
import time
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)


def job_pipeline_dia():
    """
    23:55 — Guarda todos los partidos del día con estado final.
    1 request total.
    """
    log.info("Iniciando job pipeline del día (23:55)")
    try:
        from backend.pipeline.pipeline_dia import correr_pipeline
        correr_pipeline()
        log.info("Pipeline del día completado")
    except Exception as e:
        log.error(f"Error en pipeline del día: {e}")


def job_estadisticas():
    """
    00:30 — Guarda estadísticas detalladas de los
    partidos que terminaron hoy.
    Máximo 20 requests.
    """
    log.info("Iniciando job estadísticas (00:30)")
    try:
        from backend.pipeline.job_estadisticas import correr_job_estadisticas
        correr_job_estadisticas()
        log.info("Job estadísticas completado")
    except Exception as e:
        log.error(f"Error en job estadísticas: {e}")


def job_fixtures_manana():
    """
    00:45 — Guarda los partidos del día SIGUIENTE.
    Así al despertar ya tienes los fixtures de hoy
    listos para analizar con el modelo.
    1 request total.
    """
    log.info("Iniciando job fixtures mañana (00:45)")
    try:
        from backend.pipeline.pipeline_dia import correr_pipeline_fecha
        from datetime import date, timedelta
        manana = (date.today() + timedelta(days=1)).isoformat()
        correr_pipeline_fecha(manana)
        log.info("Fixtures de mañana guardados")
    except Exception as e:
        log.error(f"Error en fixtures mañana: {e}")


def iniciar_scheduler():
    log.info("=" * 55)
    log.info("  BetML Pro — Scheduler iniciado")
    log.info("  23:55 → Partidos del día (FT)")
    log.info("  00:30 → Estadísticas de partidos")
    log.info("  00:45 → Fixtures del día siguiente")
    log.info("=" * 55)

    schedule.every().day.at("23:55").do(job_pipeline_dia)
    schedule.every().day.at("00:30").do(job_estadisticas)
    schedule.every().day.at("00:45").do(job_fixtures_manana)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    iniciar_scheduler()