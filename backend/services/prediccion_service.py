import logging
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from backend.db.modelos import Partido, Equipo
from backend.repositories.partido_repo import PartidoRepository
from backend.repositories.prediccion_repo import PrediccionRepository
from backend.services.modelo_service import get_modelo_service
from backend.core.config import get_settings
from backend.features.calculador import construir_features_partido
from backend.models.entrenador import FEATURES

log = logging.getLogger(__name__)

class PrediccionService:
    """
    Este servicio orquesta el flujo completo de las predicciones
    """

    def __init__(self, db: Session):
        self.db = db
        self.partido_repo = PartidoRepository(db)
        self.prediccion_repo = PrediccionRepository(db)
        self.modelo_service = get_modelo_service()
        self.settings = get_settings()


    def predecir(self, partido: Partido) -> dict | None:
        if not self.modelo_service.disponible:
            log.warning("Modelo no disponible")
            return None

        features = construir_features_partido(self.db, partido)
        if features is None:
            log.warning(f"Sin Historial para partido {partido.id}")
            return None

        X   = pd.DataFrame([features])[FEATURES].fillna(0)
        proba = self.modelo_service.predecir_proba(X)[0]

        prob_local = round(float(proba[0]), 4)
        prob_empate = round(float(proba[1]), 4)
        prob_visit = round(float(proba[2]), 4)

        idx_max  = int(np.argmax(proba))
        labels   = ["Local", "Empate", "Visitante"]
        pred_label = labels[idx_max]
        confianza = round(float(proba[idx_max]), 4)

        mercados = self._generar_mercados(prob_local, prob_empate, prob_visit)

        #Persiste la prediccion para trackind del MLOPS
        self.prediccion_repo.crear(
            partido_id = partido.id,
            mercado = "1X2",
            prediccion = pred_label,
            probabilidad = confianza,
            confianza = confianza,
        )

        return {
            "partido_id": partido.id,
            "prob_local": prob_local,
            "prob_empate": prob_empate,
            "prob_visitante": prob_visit,
            "prediccion": pred_label,
            "confianza": confianza,
            "mercados_recomentados": mercados,
        }

    def _generar_mercados(self, prob_l: float,
                          prob_e: float,
                          prob_v: float) -> list[dict]:
        """
        Genera lista de mercados recomendados según
        las probabilidades del modelo.
        Solo recomienda si supera el umbral configurado.
        """
        umbral = self.settings.umbral_confianza
        mercados = []

        # 1X2
        for prob, label in [(prob_l, "Local"),
                            (prob_e, "Empate"),
                            (prob_v, "Visitante")]:
            if prob >= umbral:
                mercados.append({
                    "mercado": "1X2",
                    "seleccion": label,
                    "probabilidad": prob
                })

        # Doble oportunidad
        if (prob_l + prob_e) >= 0.75:
            mercados.append({
                "mercado": "Doble Oportunidad",
                "seleccion": "1X",
                "probabilidad": round(prob_l + prob_e, 4)
            })

        if (prob_v + prob_e) >= 0.75:
            mercados.append({
                "mercado": "Doble Oportunidad",
                "seleccion": "X2",
                "probabilidad": round(prob_v + prob_e, 4)
            })

        # Ordena por probabilidad descendente
        return sorted(mercados,
                      key=lambda x: x["probabilidad"],
                      reverse=True)


    #Predecir los partidos pendientes
    def predecir_hoy(self) -> list[dict]:
        from datetime import date
        partidos = self.partido_repo.get_por_fecha(date.today())
        resultados = []
        for p in partidos:
            if p.estado in ["NS", "TDB"]:
                pred = self.predecir(p)
                if pred:
                    resultados.append(pred)
        return resultados


        