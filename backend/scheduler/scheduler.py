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
    23:55 — Cierra el día que termina Y baja los partidos del que
    empieza. 2 requests.

    Lo segundo es redundante con el job de las 00:45 a propósito: la
    agenda tenía un hueco de un día entero. Este job baja "hoy" (el día
    que está por terminar) y el de las 00:45 baja "mañana", así que los
    partidos del día en curso salían del 00:45 del día ANTERIOR. Si el
    scheduler estaba caído justo en esa ventana —pasó el día del
    deploy— ese día se quedaba sin partidos y nada lo recuperaba.
    Bajando también el día siguiente acá, hacen falta dos ventanas
    perdidas seguidas para repetirlo.
    """
    log.info("Iniciando job pipeline del día (23:55)")
    try:
        from backend.pipeline.pipeline_dia import correr_pipeline, correr_pipeline_fecha
        from datetime import timedelta
        from backend.pipeline.config import ahora_partidos

        correr_pipeline()
        manana = (ahora_partidos() + timedelta(days=1)).date().isoformat()
        correr_pipeline_fecha(manana)
        log.info("Pipeline del día completado (hoy + mañana)")
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


def job_guardar_recomendadas():
    """
    01:45 — deja registradas las recomendadas del día para que se
    cierren solas contra el resultado real. Después de job_odds (01:15)
    porque sin cuotas guardadas no hay value bets que recomendar.
    """
    log.info("Iniciando guardado de recomendadas (01:45)")
    try:
        from backend.pipeline.job_guardar_recomendadas import correr_job_guardar_recomendadas
        correr_job_guardar_recomendadas()
    except Exception as e:
        log.error(f"Error guardando recomendadas: {e}")


def job_odds_en_vivo():
    """
    Cada 20 min — cuotas en vivo (GET /odds/live, UNA sola llamada trae
    TODOS los partidos en vivo, no cuesta por fixture). Sin gastar
    request si no hay nada en vivo (ver _hay_partidos_en_vivo).

    20 min y no 5: con 100 requests/día, lo fijo ya se lleva ~47
    (fixtures 2 + estadísticas 25 + cuotas pre-partido 20) y
    job_partidos_en_vivo se lleva ~28 más en una jornada normal — a 5
    min esto solo pedía ~168/día, imposible. A 20 min son ~21 en una
    jornada de 7h de partidos, que entra en lo que sobra. Si igual se
    pone ajustado, el guardia de presupuesto lo frena solo.
    """
    log.info("Chequeando cuotas en vivo")
    try:
        from backend.pipeline.job_odds_en_vivo import correr_job_odds_en_vivo
        correr_job_odds_en_vivo()
    except Exception as e:
        log.error(f"Error chequeando cuotas en vivo: {e}")


def job_sofascore_en_vivo():
    """
    Cada 5 min — stats y jugadores en vivo desde Sofascore (xG, tiros,
    posesión, goles/tarjetas/atajadas por jugador). Sin costo de cuota
    API-Football. Solo abre el browser si hay partidos en vivo con
    sofascore_id ya anclado — ver job_sofascore_en_vivo.py.
    """
    log.info("Chequeando stats en vivo (Sofascore)")
    try:
        from backend.pipeline.sofascore.job_sofascore_en_vivo import correr_job_sofascore_en_vivo
        correr_job_sofascore_en_vivo()
    except Exception as e:
        log.error(f"Error chequeando stats en vivo Sofascore: {e}")


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
    log.info("  Cada 15 min → Alineaciones confirmadas (Sofascore, gratis)")
    log.info("  Cada 15 min → EN VIVO por Sofascore: marcador/estado/minuto + stats + jugadores")
    log.info("  Cada 2 h → Red de seguridad API-Football (partidos sin anclar en Sofascore)")
    log.info("  23:55 → Partidos del día (FT)")
    log.info("  00:30 → Estadísticas de partidos (API-Football)")
    log.info("  00:45 → Fixtures del día siguiente")
    log.info("  01:00 → Estadísticas Sofascore (xG, corners, jugadores)")
    log.info("  01:15 → Cuotas de los próximos partidos")
    log.info("  01:30 → MLOps: cerrar predicciones vs resultado real")
    log.info("  01:45 → Guardar recomendadas del día para seguimiento")
    log.info("  03:00 (diario) → Reentrenar los 4 modelos + Dixon-Coles")
    log.info("=" * 55)

    # El vivo lo lleva Sofascore (gratis). API-Football queda como RED DE
    # SEGURIDAD cada 2 horas: Sofascore solo cubre partidos con
    # sofascore_id anclado, y los que no se anclan (amistosos de ligas
    # chicas, sobre todo) se quedaban trabados en "NS" con el horario ya
    # pasado. Una sola llamada actualiza TODOS los partidos del día, así
    # que 2 horas cuesta ~6 requests diarios de los 100.
    # job_odds_en_vivo sigue fuera: ahí sí el costo no se justifica.
    schedule.every(15).minutes.do(job_alineaciones)
    schedule.every(15).minutes.do(job_sofascore_en_vivo)
    schedule.every(2).hours.do(job_partidos_en_vivo)
    schedule.every().day.at("23:55").do(job_pipeline_dia)
    schedule.every().day.at("00:30").do(job_estadisticas)
    schedule.every().day.at("00:45").do(job_fixtures_manana)
    schedule.every().day.at("01:00").do(job_sofascore_diario)
    schedule.every().day.at("01:15").do(job_odds)
    schedule.every().day.at("01:30").do(job_cerrar_predicciones)
    schedule.every().day.at("01:45").do(job_guardar_recomendadas)
    schedule.every().day.at("03:00").do(job_reentrenar_modelos)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    iniciar_scheduler()