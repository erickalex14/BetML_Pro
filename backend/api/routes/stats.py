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

    factores = cargar()
    stats["calibracion_real"] = {
        "por_mercado": {
            familia: {
                "n": d["n"],
                "declarado": d["declarado"],
                "real": d["real"],
                "factor": d["factor"],
                "desvio": round(d["real"] - d["declarado"], 4),
            }
            for familia, d in factores.items()
        },
        "minimo_por_mercado": MIN_MUESTRAS,
        "mensaje": (None if factores else
                    f"Ninguna familia de mercado llega a {MIN_MUESTRAS} "
                    f"predicciones cerradas todavía"),
    }
    return stats