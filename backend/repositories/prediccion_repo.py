from typing import Optional, Dict, List

from sqlalchemy.orm import Session
from backend.db.modelos import Prediccion

class PrediccionRepository:
    def __init__(self, db: Session):
        self.db = db

    #Crear una prediccion
    def crear(self, partido_id: int, mercado: str,
              prediccion: str, probabilidad: float,
              confianza: float) -> Prediccion:

        pred = Prediccion(
            partido_id=partido_id,
            mercado=mercado,
            prediccion=prediccion,
            probabilidad=probabilidad,
            confianza=confianza
        )
        self.db.add(pred)
        self.db.commit()
        self.db.refresh(pred)
        return pred

    #Obtener predicciones por partido
    def get_por_partido(self, partido_id: int) -> List[Prediccion]:
        return (
            self.db.query(Prediccion)
            .filter(Prediccion.partido_id == partido_id)
            .all()
        )

    #Obtener las estadisticas
    def get_stats(self) -> Dict:
        total = self.db.query(Prediccion).count()
        acertadas = self.db.query(Prediccion).filter(Prediccion.acerto == True).count()
        falladas = self.db.query(Prediccion).filter(Prediccion.acerto == False).count()
        pendientes = self.db.query(Prediccion).filter(Prediccion.acerto == None).count()

        accuracy = round(acertadas / (acertadas + falladas), 4) \
            if (acertadas + falladas) > 0 else None

        return {
            "total": total,
            "acertadas": acertadas,
            "falladas": falladas,
            "pendientes": pendientes,
            "accuracy": accuracy,
        }

    def marcar_resultado (self, partido_id: int,
                          resultado_real: str) -> None:
        predicciones = self.get_por_partido(partido_id)
        for pred in predicciones:
            pred.resultado_real = resultado_real
            pred.acerto = (pred.prediccion == resultado_real)
        self.db.commit()


