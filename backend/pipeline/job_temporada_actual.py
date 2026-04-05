import logging
from backend.pipeline import api_client
from backend.pipeline.guardador import guardar_partido
from backend.pipeline.config import LIGAS, TEMPORADA_ACTUAL
from backend.db.database import SessionLocal, crear_tablas
from backend.db.modelos import Partido, EstadisticaPartido

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

# Por día podemos gastar:
# 1 req  → fixtures de la liga
# ~20 req → stats de esos partidos
# Con 17 ligas necesitamos varios días — el job recuerda
# dónde se quedó gracias a la BD
MAX_REQUESTS = 50


def correr_job_temporada_actual():
    log.info("=" * 55)
    log.info("  Job Temporada Actual — Fixtures + Stats")
    log.info("=" * 55)

    crear_tablas()
    db = SessionLocal()
    requests_usados = 0
    partidos_nuevos = 0
    stats_nuevas = 0

    try:
        for nombre_liga, liga_id in LIGAS.items():

            if requests_usados >= MAX_REQUESTS:
                log.warning(
                    f"Límite de {MAX_REQUESTS} requests alcanzado. "
                    f"Corre mañana para continuar."
                )
                return

            temporada = TEMPORADA_ACTUAL[nombre_liga]

            log.info(f"\n>>> {nombre_liga} — temporada {temporada}")

            # ── PASO 1: Descargar fixtures FT de la temporada ──────
            data = api_client.get("/fixtures", params={
                "league": liga_id,
                "season": temporada,
                "status": "FT"
            })
            requests_usados += 1

            fixtures = data.get("response", [])
            log.info(f"  Partidos FT encontrados: {len(fixtures)}")

            if not fixtures:
                continue

            # Guarda fixtures nuevos — saltea los que ya existen
            for fixture in fixtures:
                partido_id = fixture["fixture"]["id"]
                existe = db.get(Partido, partido_id)
                if existe is None:
                    guardar_partido(db, fixture, liga_id, temporada)
                    partidos_nuevos += 1

            log.info(f"  Fixtures nuevos guardados: {partidos_nuevos}")

            # ── PASO 2: Stats de partidos FT sin estadísticas ──────
            # Busca partidos de esta liga que no tienen stats aún
            pendientes_stats = (
                db.query(Partido)
                .outerjoin(EstadisticaPartido)
                .filter(
                    Partido.liga_id   == liga_id,
                    Partido.temporada == temporada,
                    Partido.estado    == "FT",
                    EstadisticaPartido.id == None
                )
                .all()
            )

            log.info(f"  Partidos sin stats: {len(pendientes_stats)}")

            for partido in pendientes_stats:

                if requests_usados >= MAX_REQUESTS:
                    log.warning("Límite alcanzado durante stats — continuando mañana")
                    return

                data_stats = api_client.get(
                    "/fixtures/statistics",
                    params={"fixture": partido.id}
                )
                requests_usados += 1

                stats_raw = data_stats.get("response", [])

                if len(stats_raw) < 2:
                    log.warning(f"Sin stats para partido {partido.id}")
                    continue

                estadistica = _parsear_estadisticas(partido.id, stats_raw)
                db.add(estadistica)
                db.commit()
                stats_nuevas += 1

                log.info(
                    f"  Stats guardadas partido {partido.id} "
                    f"| req: {requests_usados}/{MAX_REQUESTS}"
                )

    except Exception as e:
        log.error(f"Error: {e}")
        db.rollback()
        raise

    finally:
        db.close()
        log.info("\n" + "=" * 55)
        log.info(f"  Partidos nuevos : {partidos_nuevos}")
        log.info(f"  Stats nuevas    : {stats_nuevas}")
        log.info(f"  Requests usados : {requests_usados}/{MAX_REQUESTS}")
        log.info("=" * 55)


def _parsear_estadisticas(partido_id: int, stats_raw: list) -> EstadisticaPartido:
    def extraer(team_data: dict, nombre_stat: str) -> float:
        for stat in team_data.get("statistics", []):
            if stat["type"] == nombre_stat:
                valor = stat["value"]
                if valor is None:
                    return 0.0
                if isinstance(valor, str):
                    return float(valor.replace("%", "").strip())
                return float(valor)
        return 0.0

    local = stats_raw[0]
    visit = stats_raw[1]

    return EstadisticaPartido(
        partido_id            = partido_id,
        tiros_local           = extraer(local, "Total Shots"),
        tiros_visit           = extraer(visit, "Total Shots"),
        tiros_arco_local      = extraer(local, "Shots on Goal"),
        tiros_arco_visit      = extraer(visit, "Shots on Goal"),
        posesion_local        = extraer(local, "Ball Possession"),
        posesion_visit        = extraer(visit, "Ball Possession"),
        corners_local         = extraer(local, "Corner Kicks"),
        corners_visit         = extraer(visit, "Corner Kicks"),
        amarillas_local       = extraer(local, "Yellow Cards"),
        amarillas_visit       = extraer(visit, "Yellow Cards"),
        rojas_local           = extraer(local, "Red Cards"),
        rojas_visit           = extraer(visit, "Red Cards"),
        pases_local           = extraer(local, "Total passes"),
        pases_visit           = extraer(visit, "Total passes"),
        precision_pases_local = extraer(local, "Passes accurate"),
        precision_pases_visit = extraer(visit, "Passes accurate"),
    )


if __name__ == "__main__":
    correr_job_temporada_actual()