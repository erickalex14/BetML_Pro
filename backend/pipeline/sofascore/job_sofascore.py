"""Job diario — trae stats de Sofascore para los partidos de los últimos
días que ya terminaron.

El endpoint por fecha de Sofascore (/sport/football/scheduled-events/{fecha})
está muerto (404 confirmado en vivo, no es un bug nuestro). En vez de
escanear "qué se jugó hoy en todo el mundo", este job recorre solo la
página 0 (los eventos más recientes) de cada liga+temporada en
TEMPORADAS_HISTORICAS — el mismo endpoint por-torneo que sí funciona,
usado en todo el resto del pipeline — y filtra a los últimos DIAS_ATRAS
días. Barato: una request de página por liga-temporada, ~56 requests.
"""
import logging
from datetime import date, timedelta, datetime
from backend.db.database import SessionLocal, crear_tablas
from backend.pipeline.sofascore.cliente import SofascoreCliente, TEMPORADAS_HISTORICAS
from backend.pipeline.sofascore.equipos import resolver_liga_id
from backend.pipeline.sofascore.job_historico_sofascore import procesar_evento_stats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

DIAS_ATRAS = 3  # margen de tolerancia si el job no corrió ayer


def correr_job_sofascore_diario(dias_atras: int = DIAS_ATRAS):
    log.info("=" * 55)
    log.info("  Job Sofascore Diario")
    log.info("=" * 55)

    crear_tablas()
    db = SessionLocal()
    stats_ok = 0
    jugadores_ok = 0
    no_match = 0
    ya_en_bd = 0
    corte = date.today() - timedelta(days=dias_atras)

    try:
        with SofascoreCliente(headless=True) as cliente:
            for nombre_liga, liga_id, season_id, label in TEMPORADAS_HISTORICAS:
                db_liga_id = resolver_liga_id(db, nombre_liga)
                if not db_liga_id:
                    continue

                # Página 0 = eventos más recientes de esta temporada.
                # Si la temporada ya terminó, esos eventos quedan viejos
                # y el filtro de fecha los descarta sin costo extra.
                eventos = cliente.get_partidos_liga_temporada(
                    liga_id=liga_id, temporada_id=season_id, pagina=0
                )
                if not eventos:
                    continue

                recientes = [
                    e for e in eventos
                    if e.get("status", {}).get("type") == "finished"
                    and datetime.fromtimestamp(e.get("startTimestamp", 0)).date() >= corte
                ]
                if not recientes:
                    continue

                log.info(f"\n>>> {nombre_liga} — {label}: {len(recientes)} partidos recientes")

                for evento in recientes:
                    status, stats_guardado, n_jugadores = procesar_evento_stats(
                        db, cliente, evento, db_liga_id)

                    if status == "ya_tenia":
                        ya_en_bd += 1
                    elif status == "sin_match":
                        no_match += 1
                    elif status == "procesado":
                        if stats_guardado:
                            stats_ok += 1
                        jugadores_ok += n_jugadores

    except Exception as e:
        log.error(f"Error en job Sofascore diario: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        log.info("\n" + "=" * 55)
        log.info(f"  Stats guardadas     : {stats_ok}")
        log.info(f"  Jugadores guardados : {jugadores_ok}")
        log.info(f"  Ya estaban en BD    : {ya_en_bd}")
        log.info(f"  Sin match en BD     : {no_match}")
        log.info("=" * 55)


if __name__ == "__main__":
    correr_job_sofascore_diario()
