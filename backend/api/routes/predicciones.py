from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.services.prediccion_service import PrediccionService

router = APIRouter()


@router.get("/hoy")
def predicciones_hoy(db: Session = Depends(get_db)):
    """Genera predicciones para todos los partidos de hoy."""
    service = PrediccionService(db)
    return service.predecir_hoy()