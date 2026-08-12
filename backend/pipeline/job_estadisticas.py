import logging
from backend.pipeline import api_client
from backend.db.database import SessionLocal
from backend.db.modelos import Partido, EstadisticaPartido

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

MAX_REQUESTS = 70  # reparto del presupuesto diario (100/día) — ver
                    # backend/pipeline/presupuesto.py. Se subió de 25 a
                    # 70 al sacar del scheduler los jobs EN VIVO de
                    # API-Football (ahora el vivo lo cubre Sofascore,
                    # gratis): lo fijo pasó a ser ~22 (fixtures 2 +
                    # cuotas 20), así que sobra cuota para stats.
                    # Lo que no llega a tiempo se guarda para la próxima
                    # corrida (ya lo hace el filtro de "sin stats").

# Solo traemos stats de temporadas actuales
# Plan free permite hasta 2024, los partidos de hoy
# caen en 2024 según la configuración actual
TEMPORADAS_CON_STATS = [2024, 2025, 2026]


def correr_job_estadisticas():
    log.info("=" * 50)
    log.info("Job estadísticas — iniciando")
    log.info("=" * 50)

    db = SessionLocal()
    requests_usados = 0
    stats_guardadas = 0

    try:
        partidos_pendientes = (
            db.query(Partido)
            .outerjoin(EstadisticaPartido)
            .filter(
                Partido.estado == "FT",
                Partido.temporada.in_(TEMPORADAS_CON_STATS),  # ← filtro clave
                EstadisticaPartido.id == None
            )
            .order_by(Partido.fecha.desc())  # más recientes primero
            .all()
        )

        total = len(partidos_pendientes)
        log.info(f"Partidos FT sin stats (temporada actual): {total}")

        if total == 0:
            log.info("Nada que procesar — todo al día")
            return

        for partido in partidos_pendientes:

            if requests_usados >= MAX_REQUESTS:
                restantes = total - stats_guardadas
                log.warning(
                    f"Límite de {MAX_REQUESTS} requests alcanzado. "
                    f"Quedan {restantes} partidos para la próxima ejecución."
                )
                break

            log.info(
                f"Procesando partido ID {partido.id} "
                f"| temporada {partido.temporada} "
                f"| {partido.equipo_local_id} vs {partido.equipo_visit_id}"
            )

            data = api_client.get(
                "/fixtures/statistics",
                params={"fixture": partido.id}
            )
            requests_usados += 1

            stats_raw = data.get("response", [])

            if len(stats_raw) < 2:
                log.warning(f"Sin stats para {partido.id} — saltando")
                continue

            estadistica = _parsear_estadisticas(partido.id, stats_raw)
            db.add(estadistica)
            db.commit()
            stats_guardadas += 1

            log.info(
                f"Stats guardadas ({stats_guardadas}/{total}) "
                f"— requests usados: {requests_usados}/{MAX_REQUESTS}"
            )

    except Exception as e:
        log.error(f"Error en job estadísticas: {e}")
        db.rollback()
        raise

    finally:
        db.close()
        log.info(
            f"Job finalizado — "
            f"{stats_guardadas} stats guardadas, "
            f"{requests_usados} requests usados"
        )


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
    correr_job_estadisticas()