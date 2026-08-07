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
