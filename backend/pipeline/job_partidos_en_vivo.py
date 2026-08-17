"""Refresca marcador/estado de los partidos de HOY mientras se juegan,
y cierra sus predicciones apenas terminan (en vez de esperar al job de
las 23:55-01:30). Pensado para correr cada 15-20 min todo el día.

No es un endpoint nuevo de API-Football: correr_pipeline() ya hace
upsert completo (estado, goles, goles HT) sobre partidos existentes
—guardador.py: "Si el partido ya existe (mismo ID), lo actualiza"—, así
que re-llamarlo periódicamente ES el refresco en vivo, gratis en código.

Lo único nuevo acá es CUÁNDO vale la pena gastar el request: plan
free de API-Football son 100 requests/día (verificado vía /status),
y los jobs ya agendados (pipeline_dia + fixtures_mañana + estadisticas
+ odds) ya usan ~60 de esos. Si corriera cada 15 min sin guardia,
sola esta tarea gastaría ~60-90 más. La guardia de abajo lo deja en
~0 costo cuando no hay nada que pueda haber cambiado (antes del
primer kickoff del día, después del último final)."""
import logging
from datetime import datetime
from backend.db.database import SessionLocal
from backend.db.modelos import Partido
from backend.pipeline.config import ahora_partidos, fecha_hoy_partidos, rango_utc_dia_partidos

log = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

_ESTADOS_EN_VIVO = ("1H", "HT", "2H", "ET", "P", "BT")


def _necesita_actualizacion(partidos: list, ahora: datetime) -> bool:
    """Lógica pura (sin DB) — separada para poder testearla sin que
    partidos reales de hoy en la BD contaminen el resultado."""
    # Día vacío: puede que sea un día sin fútbol, o puede que los
    # fixtures nunca se hayan bajado. Hay que ir a fijarse, y esta es la
    # ÚNICA corrida que puede recuperarlo.
    #
    # Bug real (13/08/2026): la agenda tiene un hueco de un día. El job
    # de las 23:55 baja los partidos de HOY (o sea, del día que está por
    # terminar) y el de las 00:45 los de MAÑANA. Los del día en curso
    # los tendría que haber bajado el 00:45 del día anterior; si el
    # scheduler estaba caído en esa ventana —como pasó el día del
    # deploy— ese día queda sin partidos para siempre. Antes esta
    # guardia devolvía False con la lista vacía, así que la red de
    # seguridad nunca iba a buscarlos: sin partidos no hay nada que
    # actualizar, y sin actualizar nunca hay partidos.
    if not partidos:
        return True

    for p in partidos:
        if p.estado in _ESTADOS_EN_VIVO:
            return True  # ya arrancó, seguro cambia de estado/marcador
        if p.estado == "NS" and p.fecha <= ahora:
            return True  # debería haber arrancado — falta que la API lo confirme
    return False


def _hay_algo_para_actualizar(db) -> bool:
    hoy = fecha_hoy_partidos()
    inicio, fin = rango_utc_dia_partidos(hoy)
    partidos_hoy = (
        db.query(Partido)
        .filter(Partido.fecha >= inicio, Partido.fecha < fin)
        .all()
    )
    return _necesita_actualizacion(partidos_hoy, ahora_partidos())


def correr_job_partidos_en_vivo():
    from backend.pipeline.pipeline_dia import correr_pipeline
    from backend.pipeline.job_cerrar_predicciones import correr_job_cerrar_predicciones
    from backend.pipeline.presupuesto import hay_presupuesto

    db = SessionLocal()
    try:
        if not _hay_algo_para_actualizar(db):
            log.info("Nada en vivo ni por arrancar — sin gastar request")
            return
    finally:
        db.close()

    # Prioridad alta pero no infinita — reserva 10 para que los jobs
    # nocturnos críticos (fixtures/estadísticas/odds pre-partido) no se
    # queden sin presupuesto si hoy hay partidos en vivo muchas horas.
    if not hay_presupuesto(10):
        log.warning("Presupuesto de API-Football bajo (<10) — se salta este ciclo")
        return

    log.info("Hay partidos en vivo/por arrancar — refrescando")
    correr_pipeline()  # 1 request, upsert de estado/goles de TODO el día
    correr_job_cerrar_predicciones()  # gratis (solo DB) — cierra lo que recién terminó


if __name__ == "__main__":
    correr_job_partidos_en_vivo()
