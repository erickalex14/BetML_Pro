"""Lectura de cuotas guardadas por job_odds.py — mejor cuota disponible
por mercado entre todos los bookmakers guardados."""
from sqlalchemy.orm import Session
from backend.db.modelos import Odds


def obtener_mejores_odds(db: Session, partido_id: int) -> dict:
    """{"odds_local": 1.95, ...} — la cuota más alta (mejor para el
    apostador) de cada mercado, entre todos los bookmakers guardados
    para ese partido. Vacío si job_odds.py todavía no corrió para este
    partido (partido muy lejano en el tiempo, o fuera de la ventana
    gratuita de API-Football)."""
    filas = db.query(Odds.mercado, Odds.valor).filter(Odds.partido_id == partido_id).all()

    mejores = {}
    for mercado, valor in filas:
        if mercado not in mejores or valor > mejores[mercado]:
            mejores[mercado] = valor
    return mejores


def probabilidades_mercado_1x2(db: Session, partido_id: int) -> dict | None:
    """Probabilidades implícitas sin margen cuando existen las tres cuotas.

    Es una referencia del mercado, no una señal independiente para calcular
    value/Kelly contra esas mismas cuotas.
    """
    claves = ("odds_local", "odds_empate", "odds_visitante")
    filas = db.query(Odds.bookmaker, Odds.mercado, Odds.valor).filter(
        Odds.partido_id == partido_id,
        Odds.mercado.in_(claves),
    ).all()
    por_casa = {}
    for casa, mercado, valor in filas:
        if casa in ("the-odds-api", "odds-api-io"):
            continue
        if valor > 1:
            por_casa.setdefault(casa, {})[mercado] = valor
    candidatos = []
    for casa, odds in por_casa.items():
        if all(k in odds for k in claves):
            implicitas = [1 / odds[k] for k in claves]
            total = sum(implicitas)
            if 0.98 <= total <= 1.30:
                candidatos.append((abs(total - 1), casa, implicitas, total))
    if not candidatos:
        return None
    _, casa, implicitas, margen = min(candidatos)
    return {
        "prob_local": round(implicitas[0] / margen, 4),
        "prob_empate": round(implicitas[1] / margen, 4),
        "prob_visitante": round(implicitas[2] / margen, 4),
        "margen_mercado": round(margen - 1, 4),
        "bookmaker_referencia": casa,
    }
