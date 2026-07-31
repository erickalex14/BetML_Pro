import logging
from sqlalchemy.orm import Session
from backend.db.modelos import EstadisticaSofascore, EstadisticaJugador

log = logging.getLogger(__name__)


def guardar_stats_sofascore(
    db: Session,
    stats: EstadisticaSofascore,
) -> bool:
    """
    Guarda estadísticas de Sofascore en BD.
    Si ya existen para ese partido las actualiza.
    """
    existente = (
        db.query(EstadisticaSofascore)
        .filter(EstadisticaSofascore.partido_id == stats.partido_id)
        .first()
    )

    if existente:
        log.info(f"Stats ya existen para el partido: {stats.partido_id} -Saltando")
        return False

    db.add(stats)
    db.commit()
    log.info(f"Stats guardado para el partido: {stats.partido_id}")
    return True



def guardar_jugadores(
    db: Session,
    jugadores: list,
    partido_id: int
)  -> int:
    """
    Guarda estadísticas de jugadores en BD.
    Si ya existen para ese partido los omite.
    """
    existente = (
        db.query(EstadisticaJugador)
        .filter(EstadisticaJugador.partido_id == partido_id)
        .count()
    )

    if existente > 0:
        log.info(f"Jugadores ya existen para el partido: {partido_id}")
        return 0

    for j in jugadores:
        db.add(j)

    db.commit()
    log.info(f"{len(jugadores)} jugadores guardados para el partido: {partido_id}")
    return len(jugadores)






