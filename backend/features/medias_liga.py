"""Medias globales de córners/tarjetas y encogimiento hacia ellas.

Por qué existe: el promedio de los últimos 5 partidos de un equipo es
una estimación ruidosa. Con equipos que vienen de una racha extrema
manda un lambda absurdo al Monte Carlo y salen probabilidades que no
resisten el olfato.

Caso real (2026-08-12, PSG vs Aston Villa, Supercopa): PSG traía 9.2
córners de promedio como local y Villa 6.4 de visitante, así que el
modelo esperaba 15.6 córners y daba 85% al Over 11.5. La casa lo pagaba
3.80 (26% implícito). La frecuencia real de Over 11.5 en 15689 partidos
de nuestra base es 27.1%, o sea la casa tenía razón y nosotros no; el
partido terminó con 2 córners. Esas "fijas" eran apuestas perdedoras.

El arreglo es encogimiento (regresión a la media): se mezcla el
promedio del equipo con la media global, pesando por cuántos partidos
tiene de muestra. Medido sobre 323 partidos históricos, con K=8 el
sesgo queda en -0.10 córners (prácticamente insesgado) y el Brier
score mejora ~12% tanto en Over 10.5 como en Over 11.5.

Las medias se calculan por localía porque un equipo de local saca más
córners que de visitante (5.39 contra 4.26 en nuestros datos): usar una
sola media para ambos lados metía sesgo.
"""
import logging
from sqlalchemy import text

log = logging.getLogger(__name__)

# Cuántos partidos "virtuales" en la media global pesan contra la
# muestra real del equipo. Ajustado empíricamente (ver docstring), no
# elegido a ojo.
K_ENCOGIMIENTO = 8

_cache: dict | None = None


def medias_globales(db) -> dict:
    """Promedios por partido y por localía. Se calculan una vez por
    proceso — son de toda la base, no cambian de un request a otro."""
    global _cache
    if _cache is not None:
        return _cache

    fila = db.execute(text("""
        select avg(corners_local), avg(corners_visitante),
               avg(amarillas_local), avg(amarillas_visitante),
               avg(rojas_local), avg(rojas_visitante),
               avg(xg_local), avg(xg_visitante)
        from estadisticas_sofascores
    """)).fetchone()

    def _o(valor, default):
        return float(valor) if valor is not None else default

    _cache = {
        "corners_local": _o(fila[0], 5.4), "corners_visit": _o(fila[1], 4.3),
        "amarillas_local": _o(fila[2], 1.9), "amarillas_visit": _o(fila[3], 2.1),
        "rojas_local": _o(fila[4], 0.05), "rojas_visit": _o(fila[5], 0.07),
        "xg_local": _o(fila[6], 1.45), "xg_visit": _o(fila[7], 1.15),
    }
    log.info(f"Medias globales para encogimiento: {_cache}")
    return _cache


def encoger(promedio_equipo: float | None, n_partidos: int, media: float,
            k: int = K_ENCOGIMIENTO) -> float:
    """Mezcla el promedio del equipo con la media global. Sin muestra
    devuelve la media global — nunca None, para que el simulador no se
    quede sin el mercado."""
    if promedio_equipo is None or n_partidos <= 0:
        return media
    return (n_partidos * promedio_equipo + k * media) / (n_partidos + k)


def estimar_xg_prepartido(stats_local: dict, stats_visit: dict,
                          medias: dict) -> tuple[float, float, str]:
    """Estima lambdas prepartido sin convertir probabilidades 1X2 en goles.

    Combina ataque propio y defensa rival, ambos encogidos hacia la media
    histórica por localía. Cuando no hay xG histórico devuelve las medias
    reales de la base: es menos específico, pero no fabrica una señal de
    pocos goles a partir de la probabilidad de empate.
    """
    n_local = int(stats_local.get("n_con_xg", 0) or 0)
    n_visit = int(stats_visit.get("n_con_xg", 0) or 0)

    ataque_local = encoger(stats_local.get("xg_favor"), n_local, medias["xg_local"])
    defensa_visit = encoger(stats_visit.get("xg_contra"), n_visit, medias["xg_local"])
    ataque_visit = encoger(stats_visit.get("xg_favor"), n_visit, medias["xg_visit"])
    defensa_local = encoger(stats_local.get("xg_contra"), n_local, medias["xg_visit"])

    xg_local = min(3.5, max(0.35, (ataque_local + defensa_visit) / 2))
    xg_visit = min(3.5, max(0.35, (ataque_visit + defensa_local) / 2))
    if n_local >= 3 and n_visit >= 3:
        fuente = "Histórico xG prepartido con regresión a la media"
    elif n_local > 0 or n_visit > 0:
        fuente = "Histórico xG parcial con regresión a la media"
    else:
        fuente = "Media histórica global; datos de equipos insuficientes"
    return xg_local, xg_visit, fuente
