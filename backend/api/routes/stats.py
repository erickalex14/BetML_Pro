from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.repositories.prediccion_repo import PrediccionRepository

router = APIRouter()


@router.get("/modelo")
def stats_modelo(db: Session = Depends(get_db)):
    """Métricas de rendimiento del modelo — MLOps tracking.

    Incluye "calibracion_real": qué probabilidad promedio venimos
    declarando contra qué porcentaje realmente acertamos. Si declaramos
    70% y acertamos 55%, el modelo es optimista y Kelly está calculando
    stakes más altos de lo que corresponde — es la métrica que más
    importa vigilar cuando hay plata de por medio.
    """
    from backend.models.calibracion_produccion import cargar, MIN_MUESTRAS

    repo = PrediccionRepository(db)
    stats = repo.get_stats()

    calib = cargar()
    if calib:
        stats["calibracion_real"] = {
            "n_muestras": calib["n_muestras"],
            "prob_media_declarada": round(calib["prob_media_declarada"], 4),
            "acierto_real": round(calib["acierto_real"], 4),
            "desvio": round(calib["acierto_real"] - calib["prob_media_declarada"], 4),
        }
    else:
        stats["calibracion_real"] = {
            "n_muestras": 0,
            "mensaje": f"Hacen falta {MIN_MUESTRAS} predicciones cerradas para medirlo",
        }
    return stats