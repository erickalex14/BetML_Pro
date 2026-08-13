"""Junta cuotas de varias fuentes gratis, en cascada.

La idea: cada fuente tiene un límite distinto y una cobertura distinta,
así que se las llama en orden y **cada una solo pide lo que la anterior
no pudo cubrir**. Así el cupo mensual de las que cobran por request se
gasta únicamente en los partidos que hicieron falta.

Orden y por qué:

1. **Sofascore** — sin tope de requests y cubre también amistosos (usa
   bet365). Es la principal justamente porque no tiene cupo que cuidar.
   Necesita `sofascore_id` anclado.
2. **The Odds API** — un request trae TODOS los partidos de una liga,
   así que rinde mucho por llamada. OJO con la cuenta del cupo: el
   costo es `mercados × regiones` por request, no 1. Con el plan free
   (500/mes ≈ 16/día) y pidiendo 2 mercados en 1 región, salen ~8
   ligas por día. No son 500 llamadas.
3. **Odds-API.io** — 500/día, para lo que quede afuera (amistosos de
   ligas chicas, sobre todo).
4. **API-Football** — último recurso: comparte los 100/día con todo el
   resto del pipeline, que es lo que queremos dejar de gastar.

Las fuentes que necesitan API key se saltan solas si la key no está en
el entorno, sin romper nada.

Sumar fuentes además MEJORA precios: `obtener_mejores_odds` se queda con
la cuota más alta entre bookmakers, así que más fuentes = mejores
cuotas = más value bets reales.
"""
import logging
import os
from datetime import timedelta

from backend.db.database import SessionLocal
from backend.db.modelos import Partido, Odds
from backend.pipeline.config import ahora_partidos

log = logging.getLogger(__name__)


def partidos_sin_cuotas(db, dias_adelante: int = 2) -> list:
    """Partidos por jugarse que todavía no tienen NINGUNA cuota."""
    ahora = ahora_partidos()
    inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)

    con_cuotas = {fila.partido_id for fila in db.query(Odds.partido_id).distinct().all()}

    partidos = (
        db.query(Partido)
        .filter(
            Partido.estado.in_(["NS", "TBD"]),
            Partido.fecha >= inicio,
            Partido.fecha <= inicio + timedelta(days=dias_adelante),
        )
        .order_by(Partido.fecha)
        .all()
    )
    return [p for p in partidos if p.id not in con_cuotas]


def _fuente_sofascore(db, partidos) -> int:
    from backend.pipeline.sofascore.job_odds_sofascore import correr_job_odds_sofascore
    return correr_job_odds_sofascore()


def _fuente_the_odds_api(db, partidos) -> int:
    if not os.environ.get("THE_ODDS_API_KEY"):
        log.info("The Odds API: sin THE_ODDS_API_KEY en el entorno — se salta")
        return 0
    from backend.pipeline.odds.the_odds_api import traer_cuotas
    return traer_cuotas(db, partidos)


def _fuente_odds_api_io(db, partidos) -> int:
    if not os.environ.get("ODDS_API_IO_KEY"):
        log.info("odds-api.io: sin ODDS_API_IO_KEY en el entorno — se salta")
        return 0
    from backend.pipeline.odds.odds_api_io import traer_cuotas
    return traer_cuotas(db, partidos)


def _fuente_api_football(db, partidos) -> int:
    from backend.pipeline.presupuesto import hay_presupuesto
    # Solo si sobra cuota de verdad: este es el recurso que queremos
    # dejar libre para fixtures y estadísticas.
    if not hay_presupuesto(40):
        log.info("API-Football: presupuesto ajustado (<40) — se salta")
        return 0
    from backend.pipeline.job_odds import correr_job_odds
    correr_job_odds(max_requests=min(20, len(partidos)))
    return 0  # el job loguea lo suyo; el conteo real sale del recuento de abajo


FUENTES = [
    ("Sofascore", _fuente_sofascore),
    ("The Odds API", _fuente_the_odds_api),
    ("odds-api.io", _fuente_odds_api_io),
    ("API-Football", _fuente_api_football),
]


def correr_orquestador_odds():
    log.info("=" * 55)
    log.info("  Cuotas — cascada de fuentes gratis")
    log.info("=" * 55)

    db = SessionLocal()
    try:
        for nombre, fuente in FUENTES:
            faltantes = partidos_sin_cuotas(db)
            if not faltantes:
                log.info(f"Todos los partidos tienen cuotas — no hace falta {nombre}")
                break

            log.info(f"{nombre}: {len(faltantes)} partido(s) sin cuotas")
            try:
                fuente(db, faltantes)
            except Exception as e:
                # Una fuente caída no puede tumbar a las siguientes
                log.error(f"{nombre} falló: {e}")

        restantes = partidos_sin_cuotas(db)
        total = len(partidos_sin_cuotas(db)) + db.query(Odds.partido_id).distinct().count()
        log.info(f"Quedaron {len(restantes)} partido(s) sin cuotas de ninguna fuente")
        return len(restantes)
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    correr_orquestador_odds()
