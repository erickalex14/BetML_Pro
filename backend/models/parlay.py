"""Apuestas combinadas (parlay/acumulada) — selecciones de partidos
DISTINTOS combinadas en una sola apuesta.

Distinto de kelly_portfolio.py (que combina varios MERCADOS del MISMO
partido, correlacionados y por eso necesita los escenarios de Monte
Carlo). Acá las selecciones son de partidos diferentes — no hay
correlación conocida entre el resultado de dos partidos de equipos
distintos en fechas distintas, así que se asume independencia:
probabilidad combinada = producto de las probabilidades, cuota
combinada = producto de las cuotas — la misma fórmula que usa cualquier
casa de apuestas para un acumulado.
"""
import logging
from backend.models.kelly import calcular_kelly

log = logging.getLogger(__name__)


def calcular_prediccion_combinada(selecciones: list) -> dict:
    """selecciones: [{"partido_id":, "mercado":, "prob": float}, ...]
    Probabilidad conjunta de que TODAS las selecciones acierten."""
    if not selecciones:
        return {"prob_combinada": 0.0, "n_selecciones": 0, "selecciones": []}

    prob_combinada = 1.0
    for s in selecciones:
        prob_combinada *= s["prob"]

    return {
        "prob_combinada": round(prob_combinada, 6),
        "n_selecciones": len(selecciones),
        "selecciones": [
            {"partido_id": s["partido_id"], "mercado": s["mercado"], "prob": round(s["prob"], 4)}
            for s in selecciones
        ],
    }


def calcular_parlay_kelly(selecciones: list, bankroll: float = 1000.0,
                           fraccion: float = 0.25) -> dict:
    """selecciones: [{"partido_id":, "mercado":, "prob": float, "cuota": float}, ...]

    El parlay ES una sola apuesta desde el punto de vista de Kelly (una
    vez combinadas prob y cuota), no la suma de N apuestas individuales
    — por eso se le aplica calcular_kelly() una sola vez sobre los
    valores combinados, igual que a cualquier apuesta simple."""
    if len(selecciones) < 2:
        return {"error": "Un parlay necesita 2+ selecciones — para 1 sola usá /kelly normal"}

    prediccion = calcular_prediccion_combinada(selecciones)
    prob_combinada = prediccion["prob_combinada"]

    cuota_combinada = 1.0
    for s in selecciones:
        cuota_combinada *= s["cuota"]

    kelly = calcular_kelly(prob_combinada, cuota_combinada, fraccion)
    stake_unidades = kelly["stake_kelly"] * bankroll

    return {
        **prediccion,
        "cuota_combinada": round(cuota_combinada, 2),
        "kelly": kelly,
        "stake_pct": round(kelly["stake_kelly"] * 100, 2),
        "stake_units": round(stake_unidades, 2),
        "bankroll": bankroll,
    }
