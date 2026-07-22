from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.repositories.prediccion_repo import PrediccionRepository

router = APIRouter()


@router.get("/modelo")
def stats_modelo(db: Session = Depends(get_db)):
    """Métricas de rendimiento del modelo — MLOps tracking."""
    repo = PrediccionRepository(db)
    return repo.get_stats()