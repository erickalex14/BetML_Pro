import logging
from datetime import date, timedelta
from sqlalchemy.orm import Session
from backend.db.database import SessionLocal, crear_tablas
from backend.db.modelos import Partido, EstadisticaSofascore
from backend.pipeline.sofascore import cliente
from backend.pipeline.sofascore.parser import (
    parsear_stats_partido,
    parsear_jugadores
)
from backend.pipeline.sofascore.guardador_sofascore import (
    guardar_stats_sofascore,
    guardar_jugadores
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

# Máximo de partidos a procesar por ejecución
MAX_PARTIDOS = 30


def correr_job_sofascore_diario():
    """
    Job diario — trae stats de Sofascore para los
    partidos de hoy que ya terminaron (FT).
    """
    log.info("=" * 55)
    log.info("  Job Sofascore Diario")
    log.info("=" * 55)

    crear_tablas()
    db = SessionLocal()
    procesados  = 0
    stats_ok    = 0
    jugadores_ok= 0

    try:
        hoy = date.today().isoformat()
        log.info(f"Buscando partidos FT de hoy: {hoy}")

        # Trae todos los partidos de hoy desde Sofascore
        eventos = cliente.get_partidos_fecha(hoy)

        if not eventos:
            log.info("Sin eventos en Sofascore hoy")
            return

        # Filtra solo los que terminaron
        ids_sofascore = set(cliente.LIGAS_SOFASCORE.values())

        partidos_ft = [
            e for e in eventos
            if e.get("status", {}).get("type") == "finished"
            and e.get("tournament", {}).get(
                "uniqueTournament", {}
            ).get("id") in ids_sofascore
        ]

        log.info(f"Partidos FT en nuestras ligas: {len(partidos_ft)}")

        for evento in partidos_ft:
            if procesados >= MAX_PARTIDOS:
                log.warning(f"Límite de {MAX_PARTIDOS} alcanzado")
                break

            sofascore_id = evento.get("id")
            if not sofascore_id:
                continue

            log.info(
                f"Procesando: "
                f"{evento['homeTeam']['name']} vs "
                f"{evento['awayTeam']['name']} "
                f"(ID Sofascore: {sofascore_id})"
            )

            # Busca el partido en nuestra BD por equipos y fecha
            partido = _buscar_partido_bd(db, evento)

            if not partido:
                log.warning(
                    f"Partido no encontrado en BD: {sofascore_id}")
                procesados += 1
                continue

            # Verifica si ya tiene stats
            ya_tiene = (
                db.query(EstadisticaSofascore)
                .filter(EstadisticaSofascore.partido_id == partido.id)
                .count()
            )
            if ya_tiene:
                log.info(f"Ya tiene stats: {partido.id} — saltando")
                procesados += 1
                continue

            # Trae y guarda stats del partido
            stats_raw = cliente.get_stats_partido(sofascore_id)
            if stats_raw:
                stats = parsear_stats_partido(
                    partido.id, sofascore_id, stats_raw)
                if stats and guardar_stats_sofascore(db, stats):
                    stats_ok += 1

            # Trae y guarda stats de jugadores
            lineups_raw = cliente.get_lineups_partido(sofascore_id)
            if lineups_raw:
                jugadores = parsear_jugadores(partido.id, lineups_raw)
                n = guardar_jugadores(db, jugadores, partido.id)
                jugadores_ok += n

            procesados += 1

    except Exception as e:
        log.error(f"Error en job Sofascore: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        log.info(f"Job finalizado — "
                 f"{stats_ok} stats, "
                 f"{jugadores_ok} jugadores guardados")


def _buscar_partido_bd(db: Session, evento: dict) -> Partido:
    """
    Busca un partido en nuestra BD usando los nombres
    de equipos del evento de Sofascore.
    Sofascore no comparte IDs con API-Football
    así que buscamos por nombre y fecha.
    """
    from datetime import datetime
    from backend.db.modelos import Equipo

    home_name = evento.get("homeTeam", {}).get("name", "")
    away_name = evento.get("awayTeam", {}).get("name", "")
    timestamp = evento.get("startTimestamp", 0)
    fecha     = datetime.fromtimestamp(timestamp).date()

    # Busca equipos por nombre (búsqueda parcial)
    local = (
        db.query(Equipo)
        .filter(Equipo.nombre.ilike(f"%{home_name[:8]}%"))
        .first()
    )
    visitante = (
        db.query(Equipo)
        .filter(Equipo.nombre.ilike(f"%{away_name[:8]}%"))
        .first()
    )

    if not local or not visitante:
        return None

    partido = (
        db.query(Partido)
        .filter(
            Partido.equipo_local_id == local.id,
            Partido.equipo_visit_id == visitante.id,
            Partido.fecha >= f"{fecha} 00:00:00",
            Partido.fecha <= f"{fecha} 23:59:59",
        )
        .first()
    )

    return partido


if __name__ == "__main__":
    correr_job_sofascore_diario()