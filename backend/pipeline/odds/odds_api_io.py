"""Cuotas desde odds-api.io.

Cobertura enorme (~4600 partidos no jugados en una sola llamada a
/v3/events, incluidos amistosos y ligas chicas), que es justo el hueco
que dejan Sofascore —solo partidos con sofascore_id anclado— y The Odds
API —solo ligas oficiales—.

Plan free: 100 requests/hora, 500/día. Cuesta 1 request por partido
para las cuotas, más 1 para listar eventos, así que entra cómodo.

Formato, verificado contra la API real con la key del proyecto:
  /v3/events?sport=football&apiKey=...      -> lista de eventos
  /v3/odds?eventId=..&bookmakers=..&apiKey= -> cuotas de ese evento

Las cuotas ya vienen DECIMALES pero como strings ("3.250"). Los
mercados se llaman distinto que en las otras fuentes:
  "ML"                  -> 1X2            (home/draw/away)
  "Totals"              -> goles over/under (la línea va en "hdp")
  "Both Teams To Score" -> BTTS           (yes/no)
  "Spread"              -> hándicap asiático (línea en "hdp")
  "Corners Totals"      -> córners over/under

BETANO PRIMERO, A PROPÓSITO: es la casa donde el usuario apuesta de
verdad. Una cuota mejor en otra casa infla el EV de una apuesta que no
puede hacer, así que para el mismo mercado se prefiere el precio de
Betano; el resto queda como respaldo cuando Betano no cotiza ese
mercado.
"""
import logging
import os

import requests

from backend.db.modelos import Odds

log = logging.getLogger(__name__)

BASE = "https://api.odds-api.io/v3"

# El orden importa: el primero que tenga el mercado, manda.
CASAS = ["Betano", "Bet365"]
BOOKMAKER = "odds-api-io"


def _decimal(valor) -> float | None:
    try:
        v = float(valor)
        return round(v, 3) if v > 1.0 else None
    except (TypeError, ValueError):
        return None


def _linea(hdp) -> str:
    """0.5 -> '0_5', -1.25 -> 'm1_25' (mismo formato que el resto)."""
    return str(hdp).replace(".", "_").replace("-", "m")


def parsear_bookmakers(bookmakers: dict) -> dict:
    """A las claves odds_* de kelly.py, respetando el orden de CASAS."""
    salida = {}

    def poner(clave, valor):
        # no pisar: la primera casa que lo trae (Betano) tiene prioridad
        if valor is not None and clave not in salida:
            salida[clave] = valor

    for casa in CASAS:
        for mercado in bookmakers.get(casa, []):
            nombre = mercado.get("name")
            for fila in mercado.get("odds", []):
                if nombre == "ML":
                    poner("odds_local", _decimal(fila.get("home")))
                    poner("odds_empate", _decimal(fila.get("draw")))
                    poner("odds_visitante", _decimal(fila.get("away")))

                elif nombre == "Both Teams To Score":
                    poner("odds_btts_si", _decimal(fila.get("yes")))
                    poner("odds_btts_no", _decimal(fila.get("no")))

                elif nombre in ("Totals", "Corners Totals"):
                    if fila.get("hdp") is None:
                        continue
                    prefijo = "goles" if nombre == "Totals" else "corners"
                    linea = _linea(fila["hdp"])
                    poner(f"odds_{prefijo}_over_{linea}", _decimal(fila.get("over")))
                    poner(f"odds_{prefijo}_under_{linea}", _decimal(fila.get("under")))

                elif nombre == "Spread":
                    if fila.get("hdp") is None:
                        continue
                    poner(f"odds_handicap_local_{_linea(fila['hdp'])}", _decimal(fila.get("home")))
                    poner(f"odds_handicap_visit_{_linea(-fila['hdp'])}", _decimal(fila.get("away")))

    return salida


def _buscar_evento(eventos: list, partido) -> dict | None:
    """Cruza por nombres + fecha, con la misma similitud que el anclaje
    de Sofascore (ya probada contra abreviaturas reales)."""
    from datetime import datetime, timezone, timedelta
    from backend.pipeline.sofascore.job_alineaciones import _similitud

    mejor, mejor_puntaje = None, 0.0
    for e in eventos:
        try:
            cuando = datetime.fromisoformat(e["date"].replace("Z", "+00:00")).astimezone(timezone.utc)
        except (ValueError, KeyError):
            continue
        # nuestras fechas son naive en hora de Guayaquil (UTC-5)
        if abs((partido.fecha - (cuando.replace(tzinfo=None) - timedelta(hours=5))).total_seconds()) > 3 * 3600:
            continue
        puntaje = min(_similitud(partido.equipo_local.nombre, e.get("home", "")),
                      _similitud(partido.equipo_visitante.nombre, e.get("away", "")))
        if puntaje > mejor_puntaje:
            mejor, mejor_puntaje = e, puntaje
    return mejor if mejor_puntaje >= 0.6 else None


def traer_cuotas(db, partidos: list, max_partidos: int = 60) -> int:
    api_key = os.environ.get("ODDS_API_IO_KEY")
    if not api_key:
        log.info("odds-api.io: sin ODDS_API_IO_KEY en el entorno — se salta")
        return 0

    try:
        eventos = requests.get(f"{BASE}/events",
                               params={"sport": "football", "apiKey": api_key},
                               timeout=30).json()
    except (requests.RequestException, ValueError) as e:
        log.error(f"odds-api.io: no se pudo listar eventos: {e}")
        return 0

    if not isinstance(eventos, list):
        log.error(f"odds-api.io: respuesta inesperada al listar eventos: {str(eventos)[:200]}")
        return 0

    pendientes = [e for e in eventos if e.get("status") not in ("settled", "cancelled")]
    log.info(f"odds-api.io: {len(pendientes)} eventos disponibles")

    guardados = 0
    for partido in partidos[:max_partidos]:
        evento = _buscar_evento(pendientes, partido)
        if evento is None:
            continue
        try:
            r = requests.get(f"{BASE}/odds",
                             params={"eventId": evento["id"],
                                     "bookmakers": ",".join(CASAS),
                                     "apiKey": api_key},
                             timeout=25)
            if r.status_code != 200:
                log.warning(f"odds-api.io evento {evento['id']}: HTTP {r.status_code}")
                continue
            mercados = parsear_bookmakers(r.json().get("bookmakers", {}))
        except (requests.RequestException, ValueError) as e:
            log.warning(f"odds-api.io evento {evento['id']}: {e}")
            continue

        if not mercados:
            continue

        db.query(Odds).filter(Odds.partido_id == partido.id,
                              Odds.bookmaker == BOOKMAKER).delete()
        for clave, valor in mercados.items():
            db.add(Odds(partido_id=partido.id, bookmaker=BOOKMAKER,
                        mercado=clave, valor=valor))
        db.commit()
        guardados += 1

    log.info(f"odds-api.io: {guardados} partido(s) cotizados")
    return guardados
