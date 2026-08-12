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
from datetime import datetime, timedelta
from backend.db.database import SessionLocal
from backend.db.modelos import Partido
from backend.pipeline.config import ahora_partidos

log = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

_ESTADOS_EN_VIVO = ("1H", "HT", "2H", "ET", "P", "BT")


def _necesita_actualizacion(partidos: list, ahora: datetime) -> bool:
    """Lógica pura (sin DB) — separada para poder testearla sin que
    partidos reales de hoy en la BD contaminen el resultado."""
    for p in partidos:
        if p.estado in _ESTADOS_EN_VIVO:
            return True  # ya arrancó, seguro cambia de estado/marcador
        if p.estado == "NS" and p.fecha <= ahora:
            return True  # debería haber arrancado — falta que la API lo confirme
    return False


def _hay_algo_para_actualizar(db) -> bool:
    hoy = ahora_partidos().date()
    partidos_hoy = (
        db.query(Partido)
        .filter(Partido.fecha >= datetime.combine(hoy, datetime.min.time()),
                Partido.fecha < datetime.combine(hoy, datetime.min.time()) + timedelta(days=1))
        .all()
    )
    return _necesita_actualizacion(partidos_hoy, ahora_partidos())


def correr_job_partidos_en_vivo():
    from backend.pipeline.pipeline_dia import correr_pipeline
    from backend.pipeline.job_cerrar_predicciones import correr_job_cerrar_predicciones

    db = SessionLocal()
    try:
        if not _hay_algo_para_actualizar(db):
            log.info("Nada en vivo ni por arrancar — sin gastar request")
            return
    finally:
        db.close()

    log.info("Hay partidos en vivo/por arrancar — refrescando")
    correr_pipeline()  # 1 request, upsert de estado/goles de TODO el día
    correr_job_cerrar_predicciones()  # gratis (solo DB) — cierra lo que recién terminó


if __name__ == "__main__":
    correr_job_partidos_en_vivo()
