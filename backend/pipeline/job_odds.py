"""Job de cuotas — trae odds reales de API-Football (gratis, por
fixture_id) para los partidos que todavía no se jugaron.

El plan free bloquea /odds por league+season (mismo gate que /fixtures),
pero consultando por fixture_id individual no aplica ese filtro — así
conseguimos cuotas reales de 10+ bookmakers sin plan pago. La cobertura
de cuotas por partido varía (algunos fixtures aún no tienen mercados
publicados, o son de ligas chicas sin cobertura de bookmaker) — se
guarda lo que haya, no es un error si un partido queda sin cuotas.

Traduce los nombres de mercado de API-Football a la MISMA convención de
claves que usa kelly.py (odds_local, odds_goles_over_2_5, etc) — así se
pueden pasar directo a analizar_mercados_kelly() sin traducir de nuevo.
Solo se mapean los mercados que el sistema ya sabe analizar; el resto
(hay ~150 tipos de apuesta distintos en la respuesta) se ignora.
"""
import logging
import re
from backend.pipeline import api_client
from backend.db.database import SessionLocal, crear_tablas
from backend.db.modelos import Partido, Odds

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)


def _linea_a_clave(texto: str) -> str:
    """'2.5' -> '2_5', '-1.5' -> 'm1_5', '+1.5' -> '1_5' (mismo formato
    que montecarlo.py, que nunca antepone '+' a una línea positiva)."""
    return texto.lstrip("+").replace(".", "_").replace("-", "m")


def _parsear_match_winner(valores: dict) -> dict:
    mapa = {"Home": "odds_local", "Draw": "odds_empate", "Away": "odds_visitante"}
    return {mapa[v]: float(o) for v, o in valores.items() if v in mapa}


def _parsear_over_under(valores: dict, prefijo: str) -> dict:
    salida = {}
    for valor_txt, odd in valores.items():
        m = re.match(r"(Over|Under)\s+([\d.]+)", valor_txt)
        if not m:
            continue
        lado, linea = m.group(1).lower(), _linea_a_clave(m.group(2))
        salida[f"odds_{prefijo}_{lado}_{linea}"] = float(odd)
    return salida


def _parsear_btts(valores: dict) -> dict:
    mapa = {"Yes": "odds_btts_si", "No": "odds_btts_no"}
    return {mapa[v]: float(o) for v, o in valores.items() if v in mapa}


def _parsear_handicap(valores: dict) -> dict:
    salida = {}
    for valor_txt, odd in valores.items():
        m = re.match(r"(Home|Away)\s+([+-]?[\d.]+)", valor_txt)
        if not m:
            continue
        lado = "local" if m.group(1) == "Home" else "visit"
        linea = _linea_a_clave(m.group(2))
        salida[f"odds_handicap_{lado}_{linea}"] = float(odd)
    return salida


def _parsear_1x2_periodo(valores: dict, sufijo: str) -> dict:
    mapa = {"Home": f"odds_{sufijo}_local", "Draw": f"odds_{sufijo}_empate",
            "Away": f"odds_{sufijo}_visitante"}
    return {mapa[v]: float(o) for v, o in valores.items() if v in mapa}


# nombre de apuesta (API-Football) -> función parser
MAPEO_MERCADOS = {
    "Match Winner":               lambda v: _parsear_match_winner(v),
    "Goals Over/Under":           lambda v: _parsear_over_under(v, "goles"),
    "Both Teams Score":           lambda v: _parsear_btts(v),
    "Corners Over Under":         lambda v: _parsear_over_under(v, "corners"),
    "Cards Over/Under":           lambda v: _parsear_over_under(v, "tarjetas"),
    "Asian Handicap":             lambda v: _parsear_handicap(v),
    "First Half Winner":          lambda v: _parsear_1x2_periodo(v, "1t"),
    "Second Half Winner":         lambda v: _parsear_1x2_periodo(v, "2t"),
    "Goals Over/Under First Half": lambda v: _parsear_over_under(v, "goles_1t"),
}


def _parsear_bookmaker(bookmaker: dict) -> dict:
    """{"odds_local": 1.9, ...} de un bookmaker — solo mercados mapeados."""
    resultado = {}
    for bet in bookmaker.get("bets", []):
        parser = MAPEO_MERCADOS.get(bet["name"])
        if not parser:
            continue
        valores = {v["value"]: v["odd"] for v in bet.get("values", [])}
        try:
            resultado.update(parser(valores))
        except (ValueError, KeyError):
            continue
    return resultado


def correr_job_odds(dias_adelante: int = 2, max_requests: int = 20):
    log.info("=" * 55)
    log.info("  Job Cuotas — BetML Pro")
    log.info("=" * 55)

    crear_tablas()
    db = SessionLocal()
    requests_usados = 0
    partidos_con_cuotas = 0
    mercados_guardados = 0

    try:
        from datetime import date, timedelta
        hoy = date.today()
        partidos = (
            db.query(Partido)
            .filter(
                Partido.estado.in_(["NS", "TBD"]),
                Partido.fecha >= f"{hoy} 00:00:00",
                Partido.fecha <= f"{hoy + timedelta(days=dias_adelante)} 23:59:59",
            )
            .all()
        )
        log.info(f"Partidos próximos a cotizar: {len(partidos)}")

        for partido in partidos:
            if requests_usados >= max_requests:
                log.warning(f"Límite de {max_requests} requests alcanzado — corre de nuevo para continuar")
                break

            data = api_client.get("/odds", params={"fixture": partido.id})
            requests_usados += 1

            respuesta = data.get("response", [])
            if not respuesta:
                continue

            # Consolida todos los bookmakers de esta respuesta — se
            # reemplazan las cuotas viejas de este partido (cambian
            # seguido hasta el kickoff)
            db.query(Odds).filter(Odds.partido_id == partido.id).delete()

            for bookmaker in respuesta[0].get("bookmakers", []):
                mercados = _parsear_bookmaker(bookmaker)
                for clave, valor in mercados.items():
                    db.add(Odds(
                        partido_id=partido.id,
                        bookmaker=bookmaker["name"],
                        mercado=clave,
                        valor=valor,
                    ))
                    mercados_guardados += 1

            db.commit()
            partidos_con_cuotas += 1

    except Exception as e:
        log.error(f"Error en job odds: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        log.info("\n" + "=" * 55)
        log.info(f"  Partidos con cuotas guardadas : {partidos_con_cuotas}")
        log.info(f"  Filas de cuotas guardadas     : {mercados_guardados}")
        log.info(f"  Requests usados               : {requests_usados}/{max_requests}")
        log.info("=" * 55)


if __name__ == "__main__":
    correr_job_odds()
