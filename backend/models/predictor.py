import logging
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from backend.features.calculador import construir_features_partido
from backend.db.modelos import Partido
from backend.models.entrenador import cargar_modelo
from backend.features.dataset import FEATURES_ML as FEATURES

log = logging.getLogger(__name__)


def predecir_partido(db: Session, partido: Partido) -> dict | None:
    """
    Predice el resultado de un partido dado.

    Retorna un diccionario con:
    - probabilidades para cada resultado (local/empate/visitante)
    - el resultado más probable
    - nivel de confianza
    - mercados recomendados con sus probabilidades
    """
    modelo = cargar_modelo()
    if modelo is None:
        log.error("No hay modelo entrenado — corre entrenador.py primero")
        return None

    # Construye las features del partido
    features = construir_features_partido(db, partido)
    if features is None:
        log.warning(f"Sin historial suficiente para partido {partido.id}")
        return None

    # Convierte a DataFrame — XGBoost necesita ese formato
    X = pd.DataFrame([features])[FEATURES].fillna(0)

    # Predicción de probabilidades
    # predict_proba retorna [prob_local, prob_empate, prob_visitante]
    proba = modelo.predict_proba(X)[0]

    prob_local   = round(float(proba[0]), 4)
    prob_empate  = round(float(proba[1]), 4)
    prob_visit   = round(float(proba[2]), 4)

    # Resultado más probable
    idx_max    = np.argmax(proba)
    resultados = ["Local", "Empate", "Visitante"]
    pred_label = resultados[idx_max]
    confianza  = round(float(proba[idx_max]), 4)

    # ── Mercados recomendados ───────────────────────────────
    # Umbral mínimo para recomendar un mercado: 60%
    UMBRAL = 0.60
    mercados_recomendados = []

    if prob_local > UMBRAL:
        mercados_recomendados.append({
            "mercado":      "1X2",
            "seleccion":    "Local",
            "probabilidad": prob_local
        })

    if prob_empate > UMBRAL:
        mercados_recomendados.append({
            "mercado":      "1X2",
            "seleccion":    "Empate",
            "probabilidad": prob_empate
        })

    if prob_visit > UMBRAL:
        mercados_recomendados.append({
            "mercado":      "1X2",
            "seleccion":    "Visitante",
            "probabilidad": prob_visit
        })

    # Doble oportunidad
    if (prob_local + prob_empate) > 0.75:
        mercados_recomendados.append({
            "mercado":      "Doble Oportunidad",
            "seleccion":    "1X",
            "probabilidad": round(prob_local + prob_empate, 4)
        })

    if (prob_visit + prob_empate) > 0.75:
        mercados_recomendados.append({
            "mercado":      "Doble Oportunidad",
            "seleccion":    "X2",
            "probabilidad": round(prob_visit + prob_empate, 4)
        })

    return {
        "partido_id":             partido.id,
        "prob_local":             prob_local,
        "prob_empate":            prob_empate,
        "prob_visitante":         prob_visit,
        "prediccion":             pred_label,
        "confianza":              confianza,
        "mercados_recomendados":  mercados_recomendados,
    }


def predecir_partidos_hoy(db: Session) -> list:
    """
    Predice todos los partidos de hoy que están en la BD
    con estado NS (Not Started) — los que aún no han jugado.
    """
    from datetime import date
    from backend.db.modelos import Partido

    hoy = date.today()

    partidos_hoy = (
        db.query(Partido)
        .filter(
            Partido.estado.in_(["NS", "TBD"]),
            Partido.fecha >= f"{hoy} 00:00:00",
            Partido.fecha <= f"{hoy} 23:59:59",
        )
        .all()
    )

    log.info(f"Partidos de hoy para predecir: {len(partidos_hoy)}")

    predicciones = []
    for partido in partidos_hoy:
        pred = predecir_partido(db, partido)
        if pred:
            predicciones.append(pred)

    log.info(f"Predicciones generadas: {len(predicciones)}")
    return predicciones