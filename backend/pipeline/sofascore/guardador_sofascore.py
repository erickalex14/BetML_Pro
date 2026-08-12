import logging
from sqlalchemy.orm import Session
from backend.db.modelos import EstadisticaSofascore, EstadisticaJugador

log = logging.getLogger(__name__)


def guardar_stats_sofascore(
    db: Session,
    stats: EstadisticaSofascore,
) -> bool:
    """
    Guarda estadísticas de Sofascore en BD — upsert por partido_id.

    Antes saltaba entero si ya existía una fila ("ya existen — Saltando"),
    nunca actualizaba — funcionaba para el job diario post-partido (una
    sola foto final), pero bloquea en vivo: la primera corrida guardaba
    xG/tiros del minuto 20, y todas las corridas siguientes durante el
    mismo partido quedaban sin efecto — mismo bug de fondo que tenía
    guardar_jugadores (ver docstring ahí), mismo arreglo acá.
    """
    existente = (
        db.query(EstadisticaSofascore)
        .filter(EstadisticaSofascore.partido_id == stats.partido_id)
        .first()
    )

    if existente is None:
        db.add(stats)
        db.commit()
        log.info(f"Stats guardado para el partido: {stats.partido_id}")
        return True

    for columna in EstadisticaSofascore.__table__.columns.keys():
        if columna in ("id", "partido_id"):
            continue
        setattr(existente, columna, getattr(stats, columna))
    db.commit()
    log.info(f"Stats actualizado para el partido: {stats.partido_id}")
    return True



def guardar_jugadores(
    db: Session,
    jugadores: list,
    partido_id: int
)  -> int:
    """
    Guarda estadísticas de jugadores en BD — upsert por
    (partido_id, sofascore_jugador_id), no por partido entero.

    Antes saltaba TODO el partido si ya había una sola fila guardada
    (bug real: si job_alineaciones.py guarda la alineación confirmada
    ANTES del partido, con stats en None, el job que corre DESPUÉS con
    los stats reales quedaba bloqueado para siempre — nunca actualizaba
    goles/rating/etc, se quedaba con los null pre-partido). Upsert por
    jugador es además más robusto que el skip-total ante una corrida
    parcial (crash a mitad de guardar 20 jugadores ya no bloquea un
    reintento completo).
    """
    guardados = 0
    for j in jugadores:
        existente = (
            db.query(EstadisticaJugador)
            .filter(
                EstadisticaJugador.partido_id == partido_id,
                EstadisticaJugador.sofascore_jugador_id == j.sofascore_jugador_id,
            )
            .first()
        )
        if existente is None:
            db.add(j)
        else:
            for columna in EstadisticaJugador.__table__.columns.keys():
                if columna == "id":
                    continue
                setattr(existente, columna, getattr(j, columna))
        guardados += 1

    db.commit()
    log.info(f"{guardados} jugadores guardados/actualizados para el partido: {partido_id}")
    return guardados






