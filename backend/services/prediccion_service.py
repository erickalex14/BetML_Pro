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
from backend.features.dataset import FEATURES_ML as FEATURES
from backend.models.calibracion import cargar_calibracion, calibrar_probabilidades
from backend.models.explicacion import generar_resumen, generar_resumen_h2h
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


    def predecir(self, partido: Partido, persistir: bool = False) -> dict | None:
        """persistir=True guarda la predicción para tracking de MLOps
        (ver job_cerrar_predicciones.py). False por default — Kelly,
        Monte Carlo y el resto de los endpoints llaman a predecir() como
        utilidad interna, potencialmente varias veces por partido; no
        cada llamada es "la predicción oficial del día". predecir_hoy()
        sí persiste — ese es el snapshot real a trackear."""
        if not self.modelo_service.disponible:
            log.warning("Modelo no disponible")
            return None

        features = construir_features_partido(self.db, partido)
        if features is None:
            log.warning(f"Sin Historial para partido {partido.id}")
            return None

        X   = pd.DataFrame([features])[FEATURES].fillna(0)
        proba = self.modelo_service.predecir_proba(X)[0]

        # Calibra — XGBoost no da probabilidades bien calibradas
        # (ver backend/models/calibracion.py). Kelly y el resto del
        # sistema deben ver la probabilidad calibrada, no la cruda.
        calibracion = cargar_calibracion()
        if calibracion is not None:
            proba = calibrar_probabilidades(calibracion, proba)

        prob_local = round(float(proba[0]), 4)
        prob_empate = round(float(proba[1]), 4)
        prob_visit = round(float(proba[2]), 4)

        idx_max  = int(np.argmax(proba))
        labels   = ["Local", "Empate", "Visitante"]
        pred_label = labels[idx_max]
        confianza = round(float(proba[idx_max]), 4)

        mercados = self._generar_mercados(prob_local, prob_empate, prob_visit)

        factores, resumen_h2h = [], None
        importancias_arr = self.modelo_service.feature_importances
        if importancias_arr is not None:
            importancias = dict(zip(FEATURES, importancias_arr))
            factores = generar_resumen(
                features, importancias,
                partido.equipo_local.nombre, partido.equipo_visitante.nombre,
            )
            resumen_h2h = generar_resumen_h2h(
                features, partido.equipo_local.nombre, partido.equipo_visitante.nombre,
            )

        if persistir:
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
            "mercados_recomendados": mercados,
            "factores": factores,
            "resumen_h2h": resumen_h2h,
        }

    def predecir_en_vivo(self, partido: Partido, n_simulaciones: int = 8000) -> dict | None:
        """Recalcula 1X2 y mercados de gol EN VIVO dado el marcador y
        minuto actuales — no es un modelo nuevo entrenado aparte: escala
        el xG pre-partido (Sofascore si ya hay stats en vivo, si no la
        misma heurística prob→xG que /recomendadas) por el tiempo que
        falta, simula el resto del partido con Monte Carlo, y le suma el
        marcador ya jugado antes de calcular todo (ver goles_local_base/
        visit_base en montecarlo.simular_partido). None si el partido no
        está en juego o falta el minuto — ver estimar_fraccion_restante."""
        from backend.models.montecarlo import simular_partido, estimar_fraccion_restante

        fraccion = estimar_fraccion_restante(partido.estado, partido.minuto)
        if fraccion is None:
            return None

        pred = self.predecir(partido)
        if not pred:
            return None

        stats = partido.stats_sofascore
        if stats and stats.xg_local and stats.xg_visitante:
            xg_local_total = stats.xg_local
            xg_visit_total = stats.xg_visitante
        else:
            xg_local_total = max(0.3, pred["prob_local"] * 2.5)
            xg_visit_total = max(0.3, pred["prob_visitante"] * 2.5)

        goles_local_actual = partido.goles_local or 0
        goles_visit_actual = partido.goles_visitante or 0

        montecarlo = simular_partido(
            xg_local_total * fraccion, xg_visit_total * fraccion,
            n_simulaciones=n_simulaciones,
            goles_local_base=goles_local_actual,
            goles_visit_base=goles_visit_actual,
            incluir_handicap=True,
        )

        return {
            "partido_id": partido.id,
            "estado": partido.estado,
            "minuto": partido.minuto,
            "marcador_actual": f"{goles_local_actual}-{goles_visit_actual}",
            "fraccion_restante": round(fraccion, 3),
            "prob_local": montecarlo["prob_local"],
            "prob_empate": montecarlo["prob_empate"],
            "prob_visitante": montecarlo["prob_visitante"],
            "montecarlo": montecarlo,
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
                pred = self.predecir(p, persistir=True)
                if pred:
                    resultados.append(pred)
        return resultados


        