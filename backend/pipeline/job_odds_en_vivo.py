"""Job de cuotas EN VIVO — GET /odds/live (gratis en el plan actual,
verificado en vivo el 2026-08-12: UNA sola llamada trae TODOS los
partidos en vivo con cuotas a la vez, sin costo por fixture a diferencia
de /odds pre-partido en job_odds.py).

Vocabulario de nombres de mercado DISTINTO al de /odds pre-partido (ej.
"Fulltime Result" en vez de "Match Winner", líneas de over/under en el
campo "handicap" en vez de en el texto "Over 2.5") — es un feed de otro
proveedor de cuotas, confirmado inspeccionando la respuesta real, no
asumido de la documentación.

Filtra suspended=True (mercado momentáneamente no apostable — común
mientras la pelota está en juego — no hay cuota real ahora mismo) y solo
guarda mercados de partidos que ya seguimos en BD (job_partidos_en_vivo.py
es quien mantiene estado/goles/minuto al día).
"""
import logging
from backend.pipeline import api_client
from backend.pipeline.job_odds import _linea_a_clave, _parsear_match_winner, _parsear_btts
from backend.pipeline.job_partidos_en_vivo import _ESTADOS_EN_VIVO
from backend.db.database import SessionLocal, crear_tablas
from backend.db.modelos import Partido, Odds

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)


def _parsear_over_under_vivo(valores: list, prefijo: str) -> dict:
    salida = {}
    for v in valores:
        if v.get("suspended") or v.get("handicap") is None:
            continue
        lado = str(v.get("value", "")).lower()
        if lado not in ("over", "under"):
            continue
        linea = _linea_a_clave(str(v["handicap"]))
        salida[f"odds_{prefijo}_{lado}_{linea}"] = float(v["odd"])
    return salida


def _sin_suspender(valores: list) -> dict:
    return {v["value"]: v["odd"] for v in valores if not v.get("suspended")}


# nombre de mercado (feed EN VIVO) -> función parser — vocabulario propio,
# no el mismo MAPEO_MERCADOS de job_odds.py (ver docstring del módulo)
MAPEO_MERCADOS_VIVO = {
    "Fulltime Result":     lambda vs: _parsear_match_winner(_sin_suspender(vs)),
    "Match Goals":         lambda vs: _parsear_over_under_vivo(vs, "goles"),
    "Both Teams to Score": lambda vs: _parsear_btts(_sin_suspender(vs)),
    "Total Corners":       lambda vs: _parsear_over_under_vivo(vs, "corners"),
    "Home Team Goals":     lambda vs: _parsear_over_under_vivo(vs, "goles_equipo_local"),
    "Away Team Goals":     lambda vs: _parsear_over_under_vivo(vs, "goles_equipo_visit"),
}

BOOKMAKER_VIVO = "vivo"  # etiqueta propia — el feed no viene agrupado por casa real


def _hay_partidos_en_vivo(db) -> bool:
    return db.query(Partido).filter(Partido.estado.in_(_ESTADOS_EN_VIVO)).first() is not None


def correr_job_odds_en_vivo():
    log.info("=" * 55)
    log.info("  Job Cuotas EN VIVO — BetML Pro")
    log.info("=" * 55)

    crear_tablas()
    db = SessionLocal()
    partidos_con_cuotas = 0
    mercados_guardados = 0

    try:
        if not _hay_partidos_en_vivo(db):
            log.info("Nada en vivo — sin gastar el request")
            return

        from backend.pipeline.presupuesto import hay_presupuesto
        # Prioridad más baja que job_partidos_en_vivo — cuotas en vivo es
        # la feature más nueva, la que menos duele si se salta un ciclo.
        # Reserva más alta (20) para dejarle presupuesto de sobra a todo
        # lo demás.
        if not hay_presupuesto(20):
            log.warning("Presupuesto de API-Football bajo (<20) — se salta este ciclo")
            return

        data = api_client.get("/odds/live")
        respuesta = data.get("response", [])
        log.info(f"Partidos en vivo con cuotas (API): {len(respuesta)}")

        for entrada in respuesta:
            fixture_id = entrada["fixture"]["id"]
            partido = db.get(Partido, fixture_id)
            if partido is None:
                continue  # partido en vivo que no seguimos (otra liga)

            mercados = {}
            for bet in entrada.get("odds", []):
                parser = MAPEO_MERCADOS_VIVO.get(bet["name"])
                if not parser:
                    continue
                try:
                    mercados.update(parser(bet.get("values", [])))
                except (ValueError, KeyError, TypeError):
                    continue

            if not mercados:
                continue

            db.query(Odds).filter(
                Odds.partido_id == partido.id, Odds.bookmaker == BOOKMAKER_VIVO
            ).delete()
            for clave, valor in mercados.items():
                db.add(Odds(partido_id=partido.id, bookmaker=BOOKMAKER_VIVO, mercado=clave, valor=valor))
                mercados_guardados += 1
            db.commit()
            partidos_con_cuotas += 1

    except Exception as e:
        log.error(f"Error en job odds en vivo: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        log.info("\n" + "=" * 55)
        log.info(f"  Partidos en vivo con cuotas guardadas : {partidos_con_cuotas}")
        log.info(f"  Filas de cuotas guardadas              : {mercados_guardados}")
        log.info("=" * 55)


if __name__ == "__main__":
    correr_job_odds_en_vivo()
