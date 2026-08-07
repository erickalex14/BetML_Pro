"""Resuelve si una selección de cualquier mercado ganó o perdió, dado el
resultado REAL de un partido ya terminado (FT).

Usa la misma convención de claves que Kelly/Montecarlo/job_odds.py
(odds_local, odds_goles_over_2_5, odds_btts_si, odds_handicap_local_m1_5,
odds_1t_local, etc — sin el prefijo "odds_" acá) — un solo lugar que
entiende esa convención para ir del lado "cuánto vale la cuota" al lado
"ganó o no" una vez que el partido ya se jugó.

Necesita EstadisticaSofascore para corners/tarjetas/rojas reales — si el
partido no tiene esas stats guardadas (Sofascore no llegó a ese
partido), esos mercados quedan sin resolver (None) en vez de asumir
cualquier cosa.
"""
import re
from backend.db.modelos import Partido, EstadisticaSofascore


def _stats(db, partido: Partido) -> EstadisticaSofascore | None:
    s = partido.stats_sofascore
    if isinstance(s, list):
        s = s[0] if s else None
    return s


def _resultado_1x2(gl: int, gv: int) -> str:
    return "local" if gl > gv else ("empate" if gl == gv else "visitante")


def resolver_mercado(db, partido: Partido, mercado: str) -> bool | None:
    """True si la selección ganó, False si perdió, None si no se puede
    resolver todavía (falta stat, o el mercado no se reconoce)."""
    if partido.estado != "FT" or partido.goles_local is None or partido.goles_visitante is None:
        return None

    gl, gv = partido.goles_local, partido.goles_visitante
    goles_total = gl + gv

    # 1X2
    if mercado in ("local", "empate", "visitante"):
        return mercado == _resultado_1x2(gl, gv)

    # Goles Over/Under (y Corners/Tarjetas/Rojas over/under, mismo patrón)
    m = re.match(r"(goles|corners|tarjetas|rojas)_(over|under)_([\dm_]+)$", mercado)
    if m:
        categoria, lado, linea_clave = m.groups()
        linea = float(linea_clave.replace("m", "-").replace("_", "."))

        if categoria == "goles":
            total_real = goles_total
        else:
            stats = _stats(db, partido)
            if stats is None:
                return None
            campo_local, campo_visit = {
                "corners": ("corners_local", "corners_visitante"),
                "tarjetas": ("amarillas_local", "amarillas_visitante"),
                "rojas": ("rojas_local", "rojas_visitante"),
            }[categoria]
            v_local, v_visit = getattr(stats, campo_local), getattr(stats, campo_visit)
            if v_local is None or v_visit is None:
                return None
            total_real = v_local + v_visit

        return (total_real > linea) if lado == "over" else (total_real <= linea)

    # BTTS
    if mercado in ("btts_si", "btts_no"):
        ambos_anotaron = gl > 0 and gv > 0
        return ambos_anotaron if mercado == "btts_si" else not ambos_anotaron

    # Hándicap asiático (líneas .5 no empatan; líneas enteras si pueden
    # pushear — un push no es "ganó" ni "perdió", queda sin resolver)
    m = re.match(r"handicap_(local|visit)_([\dm_]+)$", mercado)
    if m:
        lado, linea_clave = m.groups()
        linea = float(linea_clave.replace("m", "-").replace("_", "."))
        diferencia = (gl - gv) if lado == "local" else (gv - gl)
        ajustada = diferencia + linea
        if ajustada == 0:
            return None  # push
        return ajustada > 0

    # 1er / 2do tiempo — necesita goles al medio tiempo reales
    m = re.match(r"(1t|2t)_(local|empate|visitante)$", mercado)
    if m and partido.goles_local_ht is not None and partido.goles_visit_ht is not None:
        periodo, seleccion = m.groups()
        if periodo == "1t":
            gl_p, gv_p = partido.goles_local_ht, partido.goles_visit_ht
        else:
            gl_p, gv_p = gl - partido.goles_local_ht, gv - partido.goles_visit_ht
        return seleccion == _resultado_1x2(gl_p, gv_p)

    # Goles Over/Under del primer tiempo
    m = re.match(r"goles_1t_(over|under)_([\dm_]+)$", mercado)
    if m and partido.goles_local_ht is not None and partido.goles_visit_ht is not None:
        lado, linea_clave = m.groups()
        linea = float(linea_clave.replace("m", "-").replace("_", "."))
        total_ht = partido.goles_local_ht + partido.goles_visit_ht
        return (total_ht > linea) if lado == "over" else (total_ht <= linea)

    return None  # mercado no reconocido — no se resuelve a ciegas
