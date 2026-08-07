import logging
from backend.db.database import SessionLocal, crear_tablas
from backend.db.modelos import Partido, EstadisticaSofascore
from backend.pipeline.sofascore.cliente import (
    SofascoreCliente,
    TEMPORADAS_HISTORICAS
)
from backend.pipeline.sofascore.parser import (
    parsear_stats_partido,
    parsear_jugadores
)
from backend.pipeline.sofascore.guardador_sofascore import (
    guardar_stats_sofascore,
    guardar_jugadores
)
from backend.pipeline.sofascore.equipos import (
    resolver_liga_id,
    buscar_candidatos,
    anclar_si_corresponde,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

def correr_job_historico_sofascore(max_partidos: float = float("inf")):
    # max_partidos cuenta solo partidos con trabajo real (stats descargadas).
    # Los saltados (ya en BD / sin match) no consumen presupuesto: si lo
    # hicieran, cada ejecución se agotaría re-escaneando lo ya guardado
    # y nunca avanzaría a partidos nuevos.
    log.info("=" * 55)
    log.info("  Job Histórico Sofascore — Stats 23/24 + 24/25")
    log.info("=" * 55)

    crear_tablas()
    db = SessionLocal()
    procesados  = 0
    stats_ok    = 0
    jugadores_ok = 0
    no_match    = 0
    ya_en_bd    = 0

    try:
        with SofascoreCliente(headless=True) as cliente:
            for nombre_liga, liga_id, season_id, label in TEMPORADAS_HISTORICAS:

                if procesados >= max_partidos:
                    log.warning(
                        f"Límite de {max_partidos} alcanzado — "
                        f"corre de nuevo para continuar"
                    )
                    break

                log.info(f"\n>>> {nombre_liga} — {label} (season: {season_id})")

                db_liga_id = resolver_liga_id(db, nombre_liga)
                if not db_liga_id:
                    log.warning(f"  Liga '{nombre_liga}' no encontrada en BD — match sin acotar por liga")

                # Descarga partidos página por página (30 por página)
                pagina = 0
                while True:
                    if procesados >= max_partidos:
                        break

                    partidos_raw = cliente.get_partidos_liga_temporada(
                        liga_id=liga_id,
                        temporada_id=season_id,
                        pagina=pagina
                    )

                    if not partidos_raw:
                        log.info(f"  Sin más partidos en página {pagina}")
                        break

                    log.info(
                        f"  Página {pagina}: {len(partidos_raw)} partidos")

                    for evento in partidos_raw:
                        if procesados >= max_partidos:
                            break

                        status, stats_guardado, n_jugadores = procesar_evento_stats(
                            db, cliente, evento, db_liga_id)

                        if status == "no_terminado":
                            continue
                        if status == "ya_tenia":
                            ya_en_bd += 1
                            continue
                        if status == "sin_match":
                            no_match += 1
                            continue

                        # procesado
                        if stats_guardado:
                            stats_ok += 1
                        jugadores_ok += n_jugadores
                        procesados += 1

                    # Sofascore devuelve 30 partidos por página
                    # Si devolvió menos de 30, no hay más páginas
                    if len(partidos_raw) < 30:
                        break
                    pagina += 1

    except Exception as e:
        log.error(f"Error en job histórico: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        log.info("\n" + "=" * 55)
        log.info(f"  Partidos procesados : {procesados}")
        log.info(f"  Stats guardadas     : {stats_ok}")
        log.info(f"  Jugadores guardados : {jugadores_ok}")
        log.info(f"  Ya estaban en BD    : {ya_en_bd}")
        log.info(f"  Sin match en BD     : {no_match}")
        log.info("=" * 55)


def procesar_evento_stats(db, cliente, evento: dict, db_liga_id: int | None):
    """Intenta traer y guardar stats+jugadores de un evento Sofascore ya
    identificado como perteneciente a una liga nuestra. Compartido por el
    job histórico (recorre temporadas completas) y el diario (recorre solo
    página 0 de la temporada vigente).

    Devuelve (status, stats_guardado, n_jugadores) — status en
    'no_terminado' | 'ya_tenia' | 'sin_match' | 'procesado'."""
    if evento.get("status", {}).get("type") != "finished":
        return "no_terminado", False, 0

    sofascore_id = evento.get("id")
    if not sofascore_id:
        return "no_terminado", False, 0

    home_name = evento.get("homeTeam", {}).get("name", "")
    away_name = evento.get("awayTeam", {}).get("name", "")

    ya_tiene = (
        db.query(EstadisticaSofascore)
        .filter(EstadisticaSofascore.sofascore_id == sofascore_id)
        .count()
    )
    partido = _buscar_partido(db, evento, db_liga_id)

    log.debug(
        f"  ID:{sofascore_id} | ya_tiene={ya_tiene} | "
        f"partido_bd={'encontrado' if partido else 'NO encontrado'}"
    )

    if ya_tiene:
        log.debug(f"  Ya tiene stats: {sofascore_id} — saltando")
        return "ya_tenia", False, 0

    if not partido:
        log.debug(f"  No encontrado en BD: {home_name} vs {away_name}")
        return "sin_match", False, 0

    log.info(f"  Procesando: {home_name} vs {away_name} (ID Sofascore: {sofascore_id})")

    stats_guardado = False
    stats_raw = cliente.get_stats_partido(sofascore_id)
    if stats_raw:
        stats = parsear_stats_partido(partido.id, sofascore_id, stats_raw)
        if stats and guardar_stats_sofascore(db, stats):
            stats_guardado = True

    n_jugadores = 0
    lineups_raw = cliente.get_lineups_partido(sofascore_id)
    if lineups_raw:
        jugadores = parsear_jugadores(
            partido.id, lineups_raw,
            partido.equipo_local_id, partido.equipo_visit_id)
        n_jugadores = guardar_jugadores(db, jugadores, partido.id)

    return "procesado", stats_guardado, n_jugadores


def _buscar_partido(db, evento: dict, liga_id: int | None) -> Partido:
    from datetime import datetime

    timestamp = evento.get("startTimestamp", 0)
    fecha = datetime.fromtimestamp(timestamp).date()

    home = evento.get("homeTeam", {})
    away = evento.get("awayTeam", {})

    candidatos_local = buscar_candidatos(db, home.get("name", ""), home.get("id"), liga_id)
    candidatos_visit = buscar_candidatos(db, away.get("name", ""), away.get("id"), liga_id)

    if not candidatos_local or not candidatos_visit:
        return None

    partido = (
        db.query(Partido)
        .filter(
            Partido.equipo_local_id.in_([e.id for e, _ in candidatos_local]),
            Partido.equipo_visit_id.in_([e.id for e, _ in candidatos_visit]),
            Partido.fecha >= f"{fecha} 00:00:00",
            Partido.fecha <= f"{fecha} 23:59:59",
        )
        .first()
    )
    if not partido:
        return None

    # El Partido confirma cuál candidato de cada lado era el correcto.
    # Recién acá, ya desambiguado por rival+fecha, se ancla el sofascore_id.
    anclar_si_corresponde(db, candidatos_local, partido.equipo_local_id, home.get("id"))
    anclar_si_corresponde(db, candidatos_visit, partido.equipo_visit_id, away.get("id"))

    return partido


if __name__ == "__main__":
    correr_job_historico_sofascore()
