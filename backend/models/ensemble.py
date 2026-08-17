"""Ensemble — combina XGBoost, MLP, LSTM y GNN por votación ponderada.

El peso de cada modelo usa el Brier de confianza REAL reciente en producción
(predicciones ya cerradas por job_cerrar_predicciones.py, mercado
"1X2-<modelo>") — no el accuracy de validación fijo calculado una sola
vez al entrenar. Así el ensemble se auto-ajusta si un modelo empieza a
rendir distinto en producción que en el entrenamiento, sin tocar código
ni esperar al reentreno semanal. Con pocas muestras cerradas (<20) el
ruido de fútbol pesa más que la señal, así que cae al accuracy de
validación hasta juntar historial suficiente. Si un modelo no está
entrenado/disponible, se excluye del promedio en vez de fallar (así el
sistema sigue funcionando con XGBoost solo mientras MLP/LSTM todavía no
se entrenaron).
"""
import logging
import numpy as np
from sqlalchemy.orm import Session

from backend.db.modelos import Partido, Prediccion
from backend.features.calculador import construir_features_partido
from backend.models.entrenador import cargar_modelo, cargar_metricas_xgboost
from backend.models.mlp import cargar_mlp, predecir_mlp
from backend.models.lstm import cargar_lstm, predecir_lstm
from backend.models.gnn import cargar_gnn, predecir_gnn
from backend.models.calibracion import cargar_calibracion, calibrar_probabilidades
from backend.models.explicacion import generar_resumen, generar_resumen_h2h
from backend.features.dataset import FEATURES_ML
from backend.repositories.prediccion_repo import PrediccionRepository
import pandas as pd

log = logging.getLogger(__name__)

MERCADO_TRACKING = "1X2-ensemble"
MIN_MUESTRAS_PESO = 20
MAX_MUESTRAS_PESO = 200


def _peso_desde_brier(brier: float) -> float:
    """0.5 representa el Brier neutral 0.25; acota modelos extremos."""
    return max(0.1, min(0.9, 0.75 - float(brier)))


def _peso_modelo(db: Session, nombre: str, val_acc_fallback: float,
                 val_brier_fallback: float | None = None) -> float:
    filas = (db.query(Prediccion).filter(
        Prediccion.mercado == f"1X2-{nombre}",
        Prediccion.acerto.isnot(None),
        Prediccion.probabilidad.isnot(None),
    ).order_by(Prediccion.creado_en.desc()).limit(MAX_MUESTRAS_PESO).all())
    if len(filas) < MIN_MUESTRAS_PESO:
        return (_peso_desde_brier(val_brier_fallback)
                if val_brier_fallback is not None else val_acc_fallback)
    brier = np.mean([
        (float(f.probabilidad) - float(bool(f.acerto))) ** 2 for f in filas
    ])
    return _peso_desde_brier(brier)


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

        metricas_xgb = cargar_metricas_xgboost()
        peso = _peso_modelo(db, "xgboost", metricas_xgb.get("val_acc", 0.5),
                            metricas_xgb.get("val_brier"))
        predicciones.append(("xgboost", np.asarray(proba), peso))

    # ── MLP ──────────────────────────────────────────────
    cargado_mlp = cargar_mlp()
    if cargado_mlp is not None:
        pred_mlp = predecir_mlp(cargado_mlp, features)
        proba = np.array([pred_mlp["prob_local"], pred_mlp["prob_empate"], pred_mlp["prob_visitante"]])
        predicciones.append(("mlp", proba, _peso_modelo(
            db, "mlp", cargado_mlp["val_acc"], cargado_mlp.get("val_brier"))))

    # ── LSTM ─────────────────────────────────────────────
    cargado_lstm = cargar_lstm()
    if cargado_lstm is not None:
        pred_lstm = predecir_lstm(cargado_lstm, db, partido.equipo_local_id,
                                   partido.equipo_visit_id, partido.fecha)
        proba = np.array([pred_lstm["prob_local"], pred_lstm["prob_empate"], pred_lstm["prob_visitante"]])
        predicciones.append(("lstm", proba, _peso_modelo(
            db, "lstm", cargado_lstm["val_acc"], cargado_lstm.get("val_brier"))))

    # ── GNN ──────────────────────────────────────────────
    cargado_gnn = cargar_gnn()
    if cargado_gnn is not None:
        pred_gnn = predecir_gnn(cargado_gnn, partido.equipo_local_id, partido.equipo_visit_id)
        if pred_gnn is not None:  # None si algún equipo no está en el grafo (recién ascendido, etc)
            proba = np.array([pred_gnn["prob_local"], pred_gnn["prob_empate"], pred_gnn["prob_visitante"]])
            predicciones.append(("gnn", proba, _peso_modelo(
                db, "gnn", cargado_gnn["val_acc"], cargado_gnn.get("val_brier"))))

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

    # "por qué" — mismas features que vio el modelo + importancia real del
    # árbol, no un LLM inventando texto. Solo si XGBoost cargó (es el único
    # modelo con feature_importances_ interpretable de esta forma).
    factores, resumen_h2h = [], None
    if modelo_xgb is not None:
        importancias = dict(zip(FEATURES_ML, modelo_xgb.feature_importances_))
        factores = generar_resumen(
            features, importancias,
            partido.equipo_local.nombre, partido.equipo_visitante.nombre,
        )
        resumen_h2h = generar_resumen_h2h(
            features, partido.equipo_local.nombre, partido.equipo_visitante.nombre,
        )

    if persistir:
        repo = PrediccionRepository(db)
        repo.crear(
            partido_id=partido.id,
            mercado=MERCADO_TRACKING,
            prediccion=pred_label,
            probabilidad=confianza,
            confianza=confianza,
        )
        # predicción de cada modelo por separado — es lo que _peso_modelo()
        # lee después de cerrada, para reemplazar el val_acc fijo
        for nombre, proba, _ in predicciones:
            idx = int(np.argmax(proba))
            repo.crear(
                partido_id=partido.id,
                mercado=f"1X2-{nombre}",
                prediccion=etiquetas[idx],
                probabilidad=round(float(proba[idx]), 4),
                confianza=round(float(proba[idx]), 4),
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
        "factores": factores,
        "resumen_h2h": resumen_h2h,
    }
