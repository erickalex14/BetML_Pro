import logging
from backend.pipeline import api_client
from backend.db.database import SessionLocal
from backend.db.modelos import Partido, EstadisticaPartido

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

# Máximo de requests que este job puede gastar por ejecución.
# Con 20 requests podemos cubrir todos los partidos de un día
# normal sin comprometer el límite diario.
MAX_REQUESTS = 20


def correr_job_estadisticas():
    log.info("=" * 50)
    log.info("Job estadísticas — iniciando")
    log.info("=" * 50)

    db = SessionLocal()
    requests_usados = 0
    stats_guardadas = 0

    try:
        # Busca partidos terminados (FT) que NO tienen
        # estadísticas guardadas todavía.
        # outerjoin + filter None = LEFT JOIN WHERE NULL
        # Es el equivalente SQL de:
        # SELECT p.* FROM partidos p
        # LEFT JOIN estadisticas_partido e ON p.id = e.partido_id
        # WHERE p.estado = 'FT' AND e.id IS NULL
        partidos_pendientes = (
            db.query(Partido)
            .outerjoin(EstadisticaPartido)
            .filter(
                Partido.estado == "FT",
                EstadisticaPartido.id == None
            )
            .order_by(Partido.fecha.desc())  # más recientes primero
            .all()
        )

        total = len(partidos_pendientes)
        log.info(f"Partidos FT sin estadísticas: {total}")

        if total == 0:
            log.info("Nada que procesar — todo al día")
            return

        for partido in partidos_pendientes:

            # Control de presupuesto — para si llegamos al límite
            if requests_usados >= MAX_REQUESTS:
                restantes = total - stats_guardadas
                log.warning(
                    f"Límite de {MAX_REQUESTS} requests alcanzado. "
                    f"Quedan {restantes} partidos para la próxima ejecución."
                )
                break

            local     = partido.equipo_local_id
            visitante = partido.equipo_visit_id
            log.info(f"Procesando partido ID {partido.id} "
                     f"({local} vs {visitante})")

            data = api_client.get(
                "/fixtures/statistics",
                params={"fixture": partido.id}
            )
            requests_usados += 1

            stats_raw = data.get("response", [])

            if len(stats_raw) < 2:
                log.warning(f"Sin stats disponibles para {partido.id} — saltando")
                continue

            estadistica = _parsear_estadisticas(partido.id, stats_raw)

            db.add(estadistica)
            db.commit()
            stats_guardadas += 1
            log.info(f"Stats guardadas ({stats_guardadas}/{total}) "
                     f"— requests usados: {requests_usados}")

    except Exception as e:
        log.error(f"Error en job estadísticas: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        log.info(f"Job finalizado — "
                 f"{stats_guardadas} stats guardadas, "
                 f"{requests_usados} requests usados")


def _parsear_estadisticas(partido_id: int, stats_raw: list) -> EstadisticaPartido:
    """
    Convierte la respuesta cruda de la API en un objeto
    EstadisticaPartido listo para guardar en la BD.

    stats_raw[0] = estadísticas del equipo local
    stats_raw[1] = estadísticas del equipo visitante
    """

    def extraer(team_data: dict, nombre_stat: str) -> float:
        """
        Busca un stat específico dentro de la lista de estadísticas
        del equipo y retorna su valor numérico limpio.
        """
        for stat in team_data.get("statistics", []):
            if stat["type"] == nombre_stat:
                valor = stat["value"]

                if valor is None:
                    return 0.0

                # Algunos valores vienen como string "45%"
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