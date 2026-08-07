import logging
from backend.pipeline import api_client
from backend.pipeline.guardador import guardar_partido
from backend.pipeline.config import LIGAS, TORNEOS_PUNTUALES
from backend.db.database import SessionLocal, crear_tablas
from backend.db.modelos import Partido

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

TEMPORADAS = [2023, 2024, 2025]
MAX_REQUESTS = 40

# Mínimo de partidos esperados por liga y temporada.
# Si ya tenemos más de esto, la consideramos completa.
# Liga regular europeas: ~380 partidos
# Copas internacionales: ~100-130 partidos
# Ligas americanas/Asia: ~200-380 partidos
MINIMO_PARTIDOS_LIGA = {
    "Premier League":    350,
    "La Liga":           350,
    "Serie A":           350,
    "Bundesliga":        300,
    "Ligue 1":           300,
    "Champions League":  100,
    "Europa League":     100,
    "Conference League": 100,
    "Copa Libertadores": 100,
    "Copa Sudamericana": 100,
    "Liga MX":           180,
    "MLS":               250,
    "Brasileirao":       350,
    "Liga Argentina":    180,
    "LigaPro Ecuador":   150,
    "Eredivisie":        300,
    "Saudi Pro League":  200,
}


def correr_job_historico():
    log.info("=" * 55)
    log.info("  Job Histórico — Fixtures 2023 + 2024")
    log.info("=" * 55)

    crear_tablas()
    db = SessionLocal()
    requests_usados = 0
    partidos_nuevos = 0

    try:
        for temporada in TEMPORADAS:
            log.info(f"\n>>> Temporada {temporada}")
            log.info("-" * 40)

            for nombre_liga, liga_id in LIGAS.items():

                if requests_usados >= MAX_REQUESTS:
                    log.warning(
                        f"Límite de {MAX_REQUESTS} requests alcanzado. "
                        f"Corre el job mañana para continuar."
                    )
                    return

                # Cuántos partidos tenemos ya de esta liga+temporada
                existentes = (
                    db.query(Partido)
                    .filter(
                        Partido.liga_id   == liga_id,
                        Partido.temporada == temporada
                    )
                    .count()
                )

                # Umbral correcto por liga — no el genérico de 10
                minimo = MINIMO_PARTIDOS_LIGA.get(nombre_liga, 150)

                if existentes >= minimo:
                    log.info(
                        f"[{temporada}] {nombre_liga} — "
                        f"completa ({existentes}/{minimo} partidos) ✅"
                    )
                    continue

                log.info(
                    f"[{temporada}] Descargando {nombre_liga} "
                    f"({existentes} partidos actuales, "
                    f"mínimo esperado: {minimo})..."
                )

                data = api_client.get("/fixtures", params={
                    "league": liga_id,
                    "season": temporada,
                    "status": "FT"
                })
                requests_usados += 1

                fixtures = data.get("response", [])

                if not fixtures:
                    log.info(f"  → Sin partidos encontrados en la API")
                    continue

                guardados_liga = 0
                for fixture in fixtures:
                    guardar_partido(db, fixture, liga_id, temporada)
                    guardados_liga += 1
                    partidos_nuevos += 1

                log.info(
                    f"  → {guardados_liga} partidos guardados "
                    f"| requests usados: {requests_usados}/{MAX_REQUESTS}"
                )

        # Torneos puntuales (Mundial, etc.) — una sola temporada fija,
        # fuera del loop liga x temporada de arriba.
        for nombre_torneo, (liga_id, temporada) in TORNEOS_PUNTUALES.items():
            if requests_usados >= MAX_REQUESTS:
                log.warning(
                    f"Límite de {MAX_REQUESTS} requests alcanzado. "
                    f"Corre el job de nuevo para continuar."
                )
                return

            existentes = (
                db.query(Partido)
                .filter(Partido.liga_id == liga_id, Partido.temporada == temporada)
                .count()
            )
            if existentes >= 100:  # Mundial: 104 partidos en formato 48 equipos
                log.info(f"{nombre_torneo} {temporada} — completo ({existentes}) ✅")
                continue

            log.info(f"Descargando {nombre_torneo} {temporada} ({existentes} actuales)...")
            data = api_client.get("/fixtures", params={
                "league": liga_id, "season": temporada, "status": "FT"
            })
            requests_usados += 1
            for fixture in data.get("response", []):
                guardar_partido(db, fixture, liga_id, temporada)
                partidos_nuevos += 1
            log.info(f"  → {len(data.get('response', []))} partidos guardados")

        log.info("\n" + "=" * 55)
        log.info(f"  Histórico completo")
        log.info(f"  Partidos guardados : {partidos_nuevos}")
        log.info(f"  Requests usados    : {requests_usados}")
        log.info("=" * 55)

    except Exception as e:
        log.error(f"Error en job histórico: {e}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    correr_job_historico()