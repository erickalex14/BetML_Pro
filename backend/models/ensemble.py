"""Ensemble — combina XGBoost, MLP, LSTM y GNN por votación ponderada.

El peso de cada modelo es su accuracy de validación (guardada por cada
entrenador junto al modelo) — el más preciso pesa más en la decisión
final. Si un modelo no está entrenado/disponible, se excluye del
promedio en vez de fallar (así el sistema sigue funcionando con
XGBoost solo mientras MLP/LSTM todavía no se entrenaron).
"""
import logging
import numpy as np
from sqlalchemy.orm import Session

from backend.db.modelos import Partido
from backend.features.calculador import construir_features_partido
from backend.models.entrenador import cargar_modelo, cargar_metricas_xgboost
from backend.models.mlp import cargar_mlp, predecir_mlp
from backend.models.lstm import cargar_lstm, predecir_lstm
from backend.models.gnn import cargar_gnn, predecir_gnn
from backend.models.calibracion import cargar_calibracion, calibrar_probabilidades
from backend.features.dataset import FEATURES_ML
from backend.repositories.prediccion_repo import PrediccionRepository
import pandas as pd

log = logging.getLogger(__name__)

MERCADO_TRACKING = "1X2-ensemble"


def predecir_ensemble(db: Session, partido: Partido, persistir: bool = False) -> dict | None:
    """persistir=True guarda la predicción para tracking de MLOps (ver
    job_cerrar_predicciones.py) — False por default para no ensuciar esa
    tabla con llamadas de prueba/backtesting. El endpoint real de la API
    la prende explícito."""
    features = construir_features_partido(db, partido)
    if features is None:
        log.warning(f"Sin historial suficiente para partido {partido.id}")
        return None

    predicciones = []  # lista de (nombre, np.array([p_local,p_empate,p_visit]), peso)

    # ── XGBoost ──────────────────────────────────────────
    modelo_xgb = cargar_modelo()
    if modelo_xgb is not None:
        X = pd.DataFrame([features])[FEATURES_ML].fillna(0)
        proba = modelo_xgb.predict_proba(X)[0]

        calibracion = cargar_calibracion()
        if calibracion is not None:
            proba = calibrar_probabilidades(calibracion, proba)

        peso = cargar_metricas_xgboost().get("val_acc", 0.5)
        predicciones.append(("xgboost", np.asarray(proba), peso))

    # ── MLP ──────────────────────────────────────────────
    cargado_mlp = cargar_mlp()
    if cargado_mlp is not None:
        pred_mlp = predecir_mlp(cargado_mlp, features)
        proba = np.array([pred_mlp["prob_local"], pred_mlp["prob_empate"], pred_mlp["prob_visitante"]])
        predicciones.append(("mlp", proba, cargado_mlp["val_acc"]))

    # ── LSTM ─────────────────────────────────────────────
    cargado_lstm = cargar_lstm()
    if cargado_lstm is not None:
        pred_lstm = predecir_lstm(cargado_lstm, db, partido.equipo_local_id,
                                   partido.equipo_visit_id, partido.fecha)
        proba = np.array([pred_lstm["prob_local"], pred_lstm["prob_empate"], pred_lstm["prob_visitante"]])
        predicciones.append(("lstm", proba, cargado_lstm["val_acc"]))

    # ── GNN ──────────────────────────────────────────────
    cargado_gnn = cargar_gnn()
    if cargado_gnn is not None:
        pred_gnn = predecir_gnn(cargado_gnn, partido.equipo_local_id, partido.equipo_visit_id)
        if pred_gnn is not None:  # None si algún equipo no está en el grafo (recién ascendido, etc)
            proba = np.array([pred_gnn["prob_local"], pred_gnn["prob_empate"], pred_gnn["prob_visitante"]])
            predicciones.append(("gnn", proba, cargado_gnn["val_acc"]))

    if not predicciones:
        log.error("Ningún modelo disponible — corre los entrenadores primero")
        return None

    pesos = np.array([p for _, _, p in predicciones])
    pesos = pesos / pesos.sum()  # normaliza a que sumen 1

    proba_combinada = sum(w * proba for (_, proba, _), w in zip(predicciones, pesos))
    proba_combinada = proba_combinada / proba_combinada.sum()  # por si acaso

    idx_max = int(np.argmax(proba_combinada))
    etiquetas = ["Local", "Empate", "Visitante"]
    pred_label = etiquetas[idx_max]
    confianza = round(float(proba_combinada[idx_max]), 4)

    if persistir:
        PrediccionRepository(db).crear(
            partido_id=partido.id,
            mercado=MERCADO_TRACKING,
            prediccion=pred_label,
            probabilidad=confianza,
            confianza=confianza,
        )

    return {
        "partido_id": partido.id,
        "prob_local": round(float(proba_combinada[0]), 4),
        "prob_empate": round(float(proba_combinada[1]), 4),
        "prob_visitante": round(float(proba_combinada[2]), 4),
        "prediccion": pred_label,
        "confianza": confianza,
        "modelos_usados": [
            {"nombre": nombre, "peso": round(float(w), 3),
             "prob_local": round(float(p[0]), 4),
             "prob_empate": round(float(p[1]), 4),
             "prob_visitante": round(float(p[2]), 4)}
            for (nombre, p, _), w in zip(predicciones, pesos)
        ],
    }
