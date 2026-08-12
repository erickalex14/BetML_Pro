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


def job_reentrenar_modelos():
    """
    03:00 — reentrena los 4 modelos (XGBoost/MLP/LSTM/GNN) con todo el
    dataset actualizado + reajusta Dixon-Coles. Diario a pedido — un
    reentreno completo tarda ~15-20 min; con muchos partidos cerrando
    por día (más ligas/amistosos trackeados ahora) captura resultados
    frescos más rápido que semanal.
    """
    log.info("Iniciando reentrenamiento diario de modelos (03:00)")
    try:
        from backend.pipeline.job_reentrenar_modelos import correr_reentrenamiento_completo
        correr_reentrenamiento_completo()
        log.info("Reentrenamiento diario completado")
    except Exception as e:
        log.error(f"Error en reentrenamiento diario: {e}")


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


def job_cerrar_predicciones():
    """
    01:30 — MLOps: compara las predicciones guardadas con el resultado
    real de los partidos que ya terminaron. Sin esto, acerto queda NULL
    para siempre y /stats/modelo nunca calcula un accuracy real.
    """
    log.info("Iniciando job cerrar predicciones (01:30)")
    try:
        from backend.pipeline.job_cerrar_predicciones import correr_job_cerrar_predicciones
        correr_job_cerrar_predicciones()
        log.info("Job cerrar predicciones completado")
    except Exception as e:
        log.error(f"Error en job cerrar predicciones: {e}")


def job_sofascore_diario():
    """
    01:00 — Rellena con Sofascore lo que API-Football no trae: xG,
    corners, presiones, ratings y stats de jugador de los partidos que
    terminaron hoy. Corre después de job_estadisticas (00:30) — necesita
    que esos partidos ya estén guardados para poder adjuntarles stats.
    """
    log.info("Iniciando job Sofascore diario (01:00)")
    try:
        from backend.pipeline.sofascore.job_sofascore import correr_job_sofascore_diario
        correr_job_sofascore_diario()
        log.info("Job Sofascore diario completado")
    except Exception as e:
        log.error(f"Error en job Sofascore diario: {e}")


def job_odds():
    """
    01:15 — Cuotas reales (hasta 14 bookmakers, gratis vía fixture_id)
    para los partidos de los próximos días. Corre después de
    job_fixtures_manana (00:45) — necesita que esos fixtures ya estén
    guardados en BD antes de poder pedir sus cuotas.
    """
    log.info("Iniciando job cuotas (01:15)")
    try:
        from backend.pipeline.job_odds import correr_job_odds
        correr_job_odds()
        log.info("Job cuotas completado")
    except Exception as e:
        log.error(f"Error en job cuotas: {e}")


def job_partidos_en_vivo():
    """
    Cada 15 min, todo el día — refresca marcador/estado de los partidos
    de hoy mientras se juegan y cierra sus predicciones apenas terminan.
    Sin gastar requests si no hay nada en vivo ni por arrancar (ver
    _hay_algo_para_actualizar en job_partidos_en_vivo.py) — importa
    porque el plan free de API-Football es 100 requests/día y los otros
    jobs ya usan ~60.
    """
    log.info("Chequeando partidos en vivo")
    try:
        from backend.pipeline.job_partidos_en_vivo import correr_job_partidos_en_vivo
        correr_job_partidos_en_vivo()
    except Exception as e:
        log.error(f"Error chequeando partidos en vivo: {e}")


def job_alineaciones():
    """
    Cada 15 min — trae la alineación confirmada de Sofascore para
    partidos que arrancan en la próxima hora y media. Corrige que
    jugadores/predicciones usen el heurístico de "titular probable"
    (basado en partidos viejos, puede listar a alguien ya transferido)
    en vez de la alineación real apenas Sofascore la publica.
    """
    log.info("Chequeando alineaciones confirmadas")
    try:
        from backend.pipeline.sofascore.job_alineaciones import correr_job_alineaciones
        correr_job_alineaciones()
    except Exception as e:
        log.error(f"Error chequeando alineaciones: {e}")


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
    log.info("  Cada 15 min → Partidos en vivo (marcador/estado + MLOps si termina)")
    log.info("  Cada 15 min → Alineaciones confirmadas (partidos que arrancan en <90min)")
    log.info("  23:55 → Partidos del día (FT)")
    log.info("  00:30 → Estadísticas de partidos (API-Football)")
    log.info("  00:45 → Fixtures del día siguiente")
    log.info("  01:00 → Estadísticas Sofascore (xG, corners, jugadores)")
    log.info("  01:15 → Cuotas de los próximos partidos")
    log.info("  01:30 → MLOps: cerrar predicciones vs resultado real")
    log.info("  03:00 (diario) → Reentrenar los 4 modelos + Dixon-Coles")
    log.info("=" * 55)

    schedule.every(15).minutes.do(job_partidos_en_vivo)
    schedule.every(15).minutes.do(job_alineaciones)
    schedule.every().day.at("23:55").do(job_pipeline_dia)
    schedule.every().day.at("00:30").do(job_estadisticas)
    schedule.every().day.at("00:45").do(job_fixtures_manana)
    schedule.every().day.at("01:00").do(job_sofascore_diario)
    schedule.every().day.at("01:15").do(job_odds)
    schedule.every().day.at("01:30").do(job_cerrar_predicciones)
    schedule.every().day.at("03:00").do(job_reentrenar_modelos)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    iniciar_scheduler()