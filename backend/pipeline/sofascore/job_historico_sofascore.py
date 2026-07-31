import logging
from backend.db.database import SessionLocal, crear_tablas
from backend.db.modelos import Partido, EstadisticaSofascore, Equipo
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

# Partidos a procesar por ejecución
# Con 30 partidos por página y stats de cada uno
# cada ejecución tarda ~5-10 minutos
MAX_PARTIDOS_POR_EJECUCION = 500


def correr_job_historico_sofascore():
    log.info("=" * 55)
    log.info("  Job Histórico Sofascore — Stats 23/24 + 24/25")
    log.info("=" * 55)

    crear_tablas()
    db = SessionLocal()
    procesados  = 0
    stats_ok    = 0
    jugadores_ok = 0
    no_match    = 0

    try:
        with SofascoreCliente(headless=True) as cliente:
            for nombre_liga, liga_id, season_id, label in TEMPORADAS_HISTORICAS:

                if procesados >= MAX_PARTIDOS_POR_EJECUCION:
                    log.warning(
                        f"Límite de {MAX_PARTIDOS_POR_EJECUCION} alcanzado — "
                        f"corre mañana para continuar"
                    )
                    break

                log.info(f"\n>>> {nombre_liga} — {label} (season: {season_id})")

                # Descarga partidos página por página (30 por página)
                pagina = 0
                while True:
                    if procesados >= MAX_PARTIDOS_POR_EJECUCION:
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
                        if procesados >= MAX_PARTIDOS_POR_EJECUCION:
                            break

                        # Solo partidos terminados
                        if evento.get("status", {}).get("type") != "finished":
                            continue

                        sofascore_id = evento.get("id")
                        if not sofascore_id:
                            continue

                        home_name = evento.get(
                            "homeTeam", {}).get("name", "")
                        away_name = evento.get(
                            "awayTeam", {}).get("name", "")

                        # Verifica si ya tiene stats en BD
                        ya_tiene = (
                            db.query(EstadisticaSofascore)
                            .filter(
                                EstadisticaSofascore.sofascore_id == sofascore_id
                            )
                            .count()
                        )
                        if ya_tiene:
                            log.info(
                                f"  Ya tiene stats: {sofascore_id} — saltando")
                            procesados += 1
                            continue

                        # Busca el partido en nuestra BD
                        partido = _buscar_partido(
                            db, evento, home_name, away_name)

                        if not partido:
                            log.warning(
                                f"  No encontrado en BD: "
                                f"{home_name} vs {away_name}"
                            )
                            no_match += 1
                            procesados += 1
                            continue

                        log.info(
                            f"  Procesando: {home_name} vs {away_name} "
                            f"(ID Sofascore: {sofascore_id})"
                        )

                        # Trae y guarda stats del partido
                        stats_raw = cliente.get_stats_partido(sofascore_id)
                        if stats_raw:
                            stats = parsear_stats_partido(
                                partido.id, sofascore_id, stats_raw)
                            if stats and guardar_stats_sofascore(db, stats):
                                stats_ok += 1

                        # Trae y guarda stats de jugadores
                        lineups_raw = cliente.get_lineups_partido(
                            sofascore_id)
                        if lineups_raw:
                            jugadores = parsear_jugadores(
                                partido.id, lineups_raw)
                            n = guardar_jugadores(
                                db, jugadores, partido.id)
                            jugadores_ok += n

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
        log.info(f"  Sin match en BD     : {no_match}")
        log.info("=" * 55)


def _buscar_partido(db, evento: dict,
                    home_name: str, away_name: str) -> Partido:
    from datetime import datetime

    timestamp = evento.get("startTimestamp", 0)
    fecha = datetime.fromtimestamp(timestamp).date()

    # Diccionario de nombres alternativos
    # Sofascore usa nombres cortos, API-Football usa nombres completos
    NOMBRES_MAP = {
        "Wolverhampton":     "Wolverhampton",
        "Manchester City":   "Manchester City",
        "Manchester United": "Manchester United",
        "Brighton":          "Brighton",
        "Nottingham":        "Nottingham",
        "Newcastle":         "Newcastle",
        "Tottenham":         "Tottenham",
        "West Ham":          "West Ham",
        "Atletico":          "Atletico",
        "Betis":             "Betis",
        "Athletic":          "Athletic",
        "Inter":             "Inter",
        "Milan":             "AC Milan",
        "Bayer 04":          "Bayer Leverkusen",
        "Paris":             "Paris Saint-Germain",
    }

    def buscar_equipo(nombre: str):
        # Intenta primero con los primeros 5 caracteres
        equipo = (
            db.query(Equipo)
            .filter(Equipo.nombre.ilike(f"%{nombre[:5]}%"))
            .first()
        )
        if equipo:
            return equipo

        # Si no encuentra, busca palabra por palabra
        palabras = nombre.split()
        for palabra in palabras:
            if len(palabra) > 4:
                equipo = (
                    db.query(Equipo)
                    .filter(Equipo.nombre.ilike(f"%{palabra}%"))
                    .first()
                )
                if equipo:
                    return equipo
        return None

    local     = buscar_equipo(home_name)
    visitante = buscar_equipo(away_name)

    if not local or not visitante:
        return None

    return (
        db.query(Partido)
        .filter(
            Partido.equipo_local_id == local.id,
            Partido.equipo_visit_id == visitante.id,
            Partido.fecha >= f"{fecha} 00:00:00",
            Partido.fecha <= f"{fecha} 23:59:59",
        )
        .first()
    )


if __name__ == "__main__":
    correr_job_historico_sofascore()
