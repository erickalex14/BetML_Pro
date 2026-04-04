import logging
from backend.pipeline.config import LIGAS
from backend.pipeline import api_client
from backend.pipeline.guardador import guardar_partido
from backend.db.database import crear_tablas, SessionLocal

log = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

TEMPORADA = 2025


def correr_pipeline():
    log.info("=" * 50)
    log.info("Iniciando Pipeline diario de BetML Pro")
    log.info("=" * 50)

    crear_tablas()
    log.info("Tablas creadas/Ok")

    db = SessionLocal()
    total_guardados = 0

    try:
        # ── ESTRATEGIA EFICIENTE: 1 solo request para TODO el día ──
        # En vez de 17 requests (una por liga), traemos TODOS
        # los partidos del día y filtramos los de nuestras ligas.
        # 17 requests → 1 request. Ahorramos 94% del límite diario.
        from datetime import date
        hoy = date.today().isoformat()

        log.info(f"Trayendo todos los partidos del día: {hoy}")

        data = api_client.get("/fixtures", params={
            "date": hoy,
            "timezone": "America/Guayaquil"  # ajusta a tu zona
        })

        todos_los_partidos = data.get("response", [])
        log.info(f"Total partidos hoy en el mundo: {len(todos_los_partidos)}")

        # IDs de nuestras ligas para filtrar
        nuestras_ligas = set(LIGAS.values())

        # Filtra solo los partidos de nuestras ligas
        partidos_filtrados = [
            p for p in todos_los_partidos
            if p["league"]["id"] in nuestras_ligas
        ]

        log.info(f"Partidos de nuestras ligas: {len(partidos_filtrados)}")

        # Guarda cada partido en la BD
        for fixture in partidos_filtrados:
            liga_id      = fixture["league"]["id"]
            nombre_liga  = fixture["league"]["name"]
            local        = fixture["teams"]["home"]["name"]
            visitante    = fixture["teams"]["away"]["name"]
            hora         = fixture["fixture"]["date"][11:16]

            log.info(f"  [{nombre_liga}] {hora} — {local} vs {visitante}")
            guardar_partido(db, fixture, liga_id, TEMPORADA)
            total_guardados += 1

        log.info(f"Pipeline completado — {total_guardados} partidos guardados")

    except Exception as e:
        log.error(f"Error en pipeline: {e}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    correr_pipeline()