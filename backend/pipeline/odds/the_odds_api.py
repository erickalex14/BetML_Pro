"""Cuotas desde The Odds API (https://the-odds-api.com).

Rinde mucho por llamada: `/v4/sports/{sport}/odds` devuelve TODOS los
partidos próximos de esa liga, con todos sus bookmakers, en un request.

OJO CON EL CUPO — no es 1 crédito por llamada:

    costo = cantidad_de_mercados x cantidad_de_regiones

Con el plan free (500/mes ≈ 16/día) y pidiendo 2 mercados en 1 región,
son 2 créditos por liga, o sea ~8 ligas por día. Por eso se piden solo
`h2h` y `totals`, y una sola región. Agregar `spreads` sube el costo un
50% y el hándicap ya lo cubre Sofascore gratis.

La API responde con las cabeceras `x-requests-remaining` y
`x-requests-used`; se loguean para no quedarse sin cupo a ciegas.

Los nombres de equipo no coinciden exactamente con los nuestros, así
que el cruce reusa la misma similitud que el anclaje de Sofascore
(job_alineaciones._similitud), que ya está probada contra abreviaturas
y renombres reales.

Cobertura: ligas oficiales. Los amistosos normalmente NO están — para
eso quedan Sofascore y Odds-API.io.
"""
import logging
import os
from datetime import timedelta

import requests

from backend.db.modelos import Odds, Equipo

log = logging.getLogger(__name__)

BASE = "https://api.the-odds-api.com/v4"
BOOKMAKER = "the-odds-api"

# h2h = 1X2, totals = over/under de goles. Cada mercado extra multiplica
# el costo, ver docstring.
MERCADOS = "h2h,totals"
REGIONES = "eu"

# Liga nuestra -> sport_key de The Odds API. Solo las que importan;
# lo que no esté acá simplemente no se pide.
LIGAS_SPORT_KEY = {
    "Premier League": "soccer_epl",
    "La Liga": "soccer_spain_la_liga",
    "Serie A": "soccer_italy_serie_a",
    "Bundesliga": "soccer_germany_bundesliga",
    "Ligue 1": "soccer_france_ligue_one",
    "Champions League": "soccer_uefa_champs_league",
    "Europa League": "soccer_uefa_europa_league",
    "Conference League": "soccer_uefa_europa_conference_league",
    "Copa Libertadores": "soccer_conmebol_copa_libertadores",
    "Copa Sudamericana": "soccer_conmebol_copa_sudamericana",
    "Brasileirao": "soccer_brazil_campeonato",
    "Liga Argentina": "soccer_argentina_primera_division",
    "MLS": "soccer_usa_mls",
    "Eredivisie": "soccer_netherlands_eredivisie",
}


def _similitud(a: str, b: str) -> float:
    from backend.pipeline.sofascore.job_alineaciones import _similitud as sim
    return sim(a, b)


def _decimal(valor) -> float | None:
    try:
        v = float(valor)
        return round(v, 3) if v > 1.0 else None
    except (TypeError, ValueError):
        return None


def _parsear_evento(evento: dict) -> dict:
    """Del JSON de un evento a las claves odds_* que usa kelly.py.

    Se queda con la MEJOR cuota entre bookmakers para cada mercado —
    igual criterio que obtener_mejores_odds."""
    salida = {}
    home = evento.get("home_team", "")

    for casa in evento.get("bookmakers", []):
        for mercado in casa.get("markets", []):
            clave_mercado = mercado.get("key")

            if clave_mercado == "h2h":
                for opcion in mercado.get("outcomes", []):
                    precio = _decimal(opcion.get("price"))
                    if precio is None:
                        continue
                    nombre = opcion.get("name", "")
                    if nombre == "Draw":
                        destino = "odds_empate"
                    elif _similitud(nombre, home) >= 0.78:
                        destino = "odds_local"
                    else:
                        destino = "odds_visitante"
                    salida[destino] = max(salida.get(destino, 0), precio)

            elif clave_mercado == "totals":
                for opcion in mercado.get("outcomes", []):
                    precio = _decimal(opcion.get("price"))
                    punto = opcion.get("point")
                    if precio is None or punto is None:
                        continue
                    lado = str(opcion.get("name", "")).lower()  # "Over"/"Under"
                    if lado not in ("over", "under"):
                        continue
                    linea = str(punto).replace(".", "_").replace("-", "m")
                    destino = f"odds_goles_{lado}_{linea}"
                    salida[destino] = max(salida.get(destino, 0), precio)

    return salida


def _buscar_partido(partidos, evento) -> object | None:
    """Cruza por nombres de equipo + fecha cercana."""
    from datetime import datetime, timezone

    inicio = evento.get("commence_time")
    if not inicio:
        return None
    try:
        cuando = datetime.fromisoformat(inicio.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None

    home, away = evento.get("home_team", ""), evento.get("away_team", "")
    mejor, mejor_puntaje = None, 0.0
    for p in partidos:
        # las fechas nuestras son naive en hora de Guayaquil (UTC-5)
        diferencia = abs((p.fecha - cuando.replace(tzinfo=None) + timedelta(hours=5)).total_seconds())
        if diferencia > 3 * 3600:
            continue
        puntaje = min(_similitud(p.equipo_local.nombre, home),
                      _similitud(p.equipo_visitante.nombre, away))
        if puntaje > mejor_puntaje:
            mejor, mejor_puntaje = p, puntaje
    return mejor if mejor_puntaje >= 0.6 else None


def traer_cuotas(db, partidos: list) -> int:
    """Pide una vez por liga presente entre los partidos sin cuotas."""
    api_key = os.environ.get("THE_ODDS_API_KEY")
    if not api_key:
        return 0

    from backend.db.modelos import Liga

    ligas = {}
    for p in partidos:
        liga = db.get(Liga, p.liga_id)
        if not liga:
            continue
        sport_key = LIGAS_SPORT_KEY.get(liga.nombre)
        if sport_key:
            ligas.setdefault(sport_key, []).append(p)

    if not ligas:
        log.info("The Odds API: ninguna liga de las que faltan está mapeada")
        return 0

    guardados = 0
    for sport_key, sus_partidos in ligas.items():
        try:
            r = requests.get(
                f"{BASE}/sports/{sport_key}/odds",
                params={"apiKey": api_key, "regions": REGIONES,
                        "markets": MERCADOS, "oddsFormat": "decimal"},
                timeout=20,
            )
        except requests.RequestException as e:
            log.error(f"The Odds API ({sport_key}): {e}")
            continue

        if r.status_code != 200:
            log.error(f"The Odds API ({sport_key}): HTTP {r.status_code} — {r.text[:200]}")
            continue

        restantes = r.headers.get("x-requests-remaining")
        usados = r.headers.get("x-requests-used")
        log.info(f"The Odds API ({sport_key}): creditos usados={usados} restantes={restantes}")

        for evento in r.json():
            partido = _buscar_partido(sus_partidos, evento)
            if partido is None:
                continue
            mercados = _parsear_evento(evento)
            if not mercados:
                continue
            db.query(Odds).filter(Odds.partido_id == partido.id,
                                  Odds.bookmaker == BOOKMAKER).delete()
            for clave, valor in mercados.items():
                db.add(Odds(partido_id=partido.id, bookmaker=BOOKMAKER,
                            mercado=clave, valor=valor))
            db.commit()
            guardados += 1

    log.info(f"The Odds API: {guardados} partido(s) cotizados")
    return guardados
