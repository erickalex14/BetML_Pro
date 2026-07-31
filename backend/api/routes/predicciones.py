from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.services.prediccion_service import PrediccionService
from backend.models.kelly import analizar_mercados_kelly

router = APIRouter()


@router.get("/hoy")
def predicciones_hoy(db: Session = Depends(get_db)):
    service = PrediccionService(db)
    return service.predecir_hoy()


@router.get("/{partido_id}/kelly")
def kelly_partido(
    partido_id: int,
    odds_local:     float = 2.0,
    odds_empate:    float = 3.5,
    odds_visitante: float = 4.0,
    bankroll:       float = 1000.0,
    fraccion:       float = 0.25,
    db: Session = Depends(get_db)
):
    """
    Calcula el stake óptimo con Kelly Criterion para un partido.

    Parámetros query:
      odds_local, odds_empate, odds_visitante → cuotas del bookmaker
      bankroll   → capital disponible (default 1000)
      fraccion   → fracción de Kelly (default 0.25 = Kelly cuarto)

    Ejemplo:
      GET /predicciones/123/kelly?odds_local=2.10&odds_empate=3.40&odds_visitante=4.50&bankroll=500
    """
    from backend.repositories.partido_repo import PartidoRepository
    from backend.services.prediccion_service import PrediccionService

    repo    = PartidoRepository(db)
    partido = repo.get_por_id(partido_id)

    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    # Genera predicción del modelo ML
    service = PrediccionService(db)
    pred    = service.predecir(partido)

    if not pred:
        raise HTTPException(
            status_code=422,
            detail="Sin historial suficiente para predecir"
        )

    # Calcula Kelly con las cuotas del bookmaker
    odds = {
        "odds_local":     odds_local,
        "odds_empate":    odds_empate,
        "odds_visitante": odds_visitante,
    }

    kelly = analizar_mercados_kelly(
        prediccion=pred,
        odds=odds,
        bankroll=bankroll,
        fraccion=fraccion,
    )

    return {
        "partido_id":  partido_id,
        "prediccion":  pred,
        "kelly":       kelly,
        "instrucciones": {
            "value_bets":  kelly["value_bets"],
            "resumen":     f"{kelly['n_value_bets']} apuesta(s) con valor positivo",
        }
    }