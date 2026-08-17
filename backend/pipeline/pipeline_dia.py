import logging
from backend.pipeline import api_client
from backend.pipeline.guardador import guardar_partido
from backend.db.database import crear_tablas, SessionLocal
from backend.pipeline.config import LIGAS, TEMPORADA_ACTUAL, fecha_hoy_partidos

log = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

TEMPORADA = 2025

def correr_pipeline_fecha(fecha: str):
    """
    Igual que correr_pipeline() pero para una fecha específica.
    Se usa para pre-cargar los fixtures del día siguiente.
    """
    log.info(f"Trayendo fixtures para fecha: {fecha}")

    crear_tablas()
    poblar_ligas()

    db = SessionLocal()
    total_guardados = 0

    try:
        data = api_client.get("/fixtures", params={
            "date":     fecha,
            "timezone": "America/Guayaquil"
        })

        todos = data.get("response", [])
        nuestras_ligas = set(LIGAS.values())
        filtrados = [p for p in todos if p["league"]["id"] in nuestras_ligas]

        log.info(f"Fixtures encontrados para {fecha}: {len(filtrados)}")

        for fixture in filtrados:
            liga_id = fixture["league"]["id"]
            guardar_partido(db, fixture, liga_id, TEMPORADA_ACTUAL.get(
                next(k for k, v in LIGAS.items() if v == liga_id), 2025
            ))
            total_guardados += 1

        log.info(f"Fixtures guardados: {total_guardados}")

    except Exception as e:
        log.error(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def poblar_ligas():
    """
    Llena la tabla ligas con los datos del diccionario LIGAS.
    Solo inserta si la liga no existe ya — no duplica.
    """
    from backend.db.modelos import Liga
    db = SessionLocal()
    try:
        for nombre, liga_id in LIGAS.items():
            existe = db.get(Liga, liga_id)
            if existe is None:
                liga = Liga(
                    id       = liga_id,
                    nombre   = nombre,
                    temporada= TEMPORADA,
                    activa   = True
                )
                db.add(liga)
                log.info(f"Liga agregada: {nombre}")
        db.commit()
        log.info("Tabla ligas poblada OK")
    finally:
        db.close()

def correr_pipeline():
    log.info("=" * 50)
    log.info("Iniciando Pipeline diario de BetML Pro")
    log.info("=" * 50)

    crear_tablas()
    log.info("Tablas creadas/Ok")

    poblar_ligas()


    db = SessionLocal()
    total_guardados = 0

    try:
        # ── ESTRATEGIA EFICIENTE: 1 solo request para TODO el día ──
        # En vez de 17 requests (una por liga), traemos TODOS
        # los partidos del día y filtramos los de nuestras ligas.
        # 17 requests → 1 request. Ahorramos 94% del límite diario.
        hoy = fecha_hoy_partidos().isoformat()

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
        from backend.services.cache import invalidar_cache_dia
        invalidar_cache_dia(db)

    except Exception as e:
        log.error(f"Error en pipeline: {e}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    correr_pipeline()
