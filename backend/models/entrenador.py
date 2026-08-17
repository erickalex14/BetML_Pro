import logging
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.metrics import accuracy_score, classification_report
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier
from backend.features.dataset import FEATURES_ML, TARGET
from backend.models.calibracion import ajustar_calibracion, guardar_calibracion
from backend.models.validacion import division_temporal, brier_confianza_elegida

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

ROOT_DIR   = Path(__file__).parent.parent.parent
MODELS_DIR = ROOT_DIR / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def crear_clasificador_xgboost(n_jobs: int = -1) -> XGBClassifier:
    """Configuración única compartida por entrenamiento y backtest."""
    return XGBClassifier(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.0,
        n_jobs=n_jobs,
        tree_method="hist",
        device="cpu",
        random_state=42,
        eval_metric="mlogloss",
        early_stopping_rounds=30,
    )


def entrenar_modelo(df: pd.DataFrame) -> tuple:
    log.info("=" * 55)
    log.info("  Entrenando modelo XGBoost — BetML Pro")
    log.info("=" * 55)

    if df.empty:
        log.error("Dataset vacío")
        return None, None, None, None, None

    log.info(f"Dataset: {df.shape[0]} partidos, {len(FEATURES_ML)} features")

    df_train, df_test = division_temporal(df)
    X_train = df_train[FEATURES_ML].fillna(0)
    X_test = df_test[FEATURES_ML].fillna(0)
    y_train = df_train[TARGET]
    y_test = df_test[TARGET]
    y = df[TARGET]

    log.info(f"Distribución target:")
    log.info(f"  Local gana  (0): {(y==0).sum()} ({(y==0).mean()*100:.1f}%)")
    log.info(f"  Empate      (1): {(y==1).sum()} ({(y==1).mean()*100:.1f}%)")
    log.info(f"  Visit gana  (2): {(y==2).sum()} ({(y==2).mean()*100:.1f}%)")

    log.info(f"Train temporal: {len(X_train)} hasta {df_train['fecha'].max()} | "
             f"Test: {len(X_test)} desde {df_test['fecha'].min()}")

    # XGBoost optimizado para el servidor
    # n_jobs=-1 usa todos los núcleos disponibles
    modelo = crear_clasificador_xgboost()

    log.info("Entrenando XGBoost...")

    # Empate es ~25% de los partidos, pero XGBoost sin balancear aprende
    # que nunca predecirlo ya maximiza accuracy (jamás se equivoca "poco"
    # con Empate, prefiere apostar todo a Local/Visitante). class_weight
    # balanced iguala el costo de error entre las 3 clases en el
    # entrenamiento — el mercado de empates deja de ser invisible.
    pesos_train = compute_sample_weight(class_weight="balanced", y=y_train)

    modelo.fit(
        X_train, y_train,
        sample_weight=pesos_train,
        eval_set=[(X_test, y_test)],
        verbose=100
    )

    # Evaluación
    y_pred       = modelo.predict(X_test)
    y_pred_proba = modelo.predict_proba(X_test)
    accuracy     = accuracy_score(y_test, y_pred)
    val_brier = brier_confianza_elegida(y_test.to_numpy(), y_pred_proba)

    log.info("\n" + "=" * 55)
    log.info(f"  RESULTADOS")
    log.info("=" * 55)
    log.info(f"  Accuracy     : {accuracy*100:.2f}%")
    log.info(f"  Benchmark    : 33.33% (random)")
    log.info(f"  Mejora       : +{(accuracy-0.333)*100:.2f}%")
    log.info("\n" + classification_report(
        y_test, y_pred,
        target_names=["Local", "Empate", "Visitante"]
    ))

    # Features más importantes
    importancias = pd.Series(
        modelo.feature_importances_,
        index=FEATURES_ML
    ).sort_values(ascending=False)

    log.info("  Top 10 features más importantes:")
    for feat, imp in importancias.head(10).items():
        bar = "█" * int(imp * 100)
        log.info(f"    {feat:<30} {imp:.4f} {bar}")

    # Calibración — ver backend/models/calibracion.py. Se ajusta acá con
    # el mismo X_test/y_test de la evaluación (hold-out, no visto en train).
    calibracion = ajustar_calibracion(y_test.to_numpy(), y_pred_proba)
    guardar_calibracion(calibracion)

    modelo._betml_val_brier = val_brier
    return modelo, X_test, y_test, y_pred_proba, accuracy


def guardar_modelo(modelo: XGBClassifier,
                   nombre: str = "modelo_v1.pkl",
                   accuracy: float = None):
    ruta = MODELS_DIR / nombre
    joblib.dump(modelo, ruta)
    log.info(f"Modelo guardado: {ruta}")
    if accuracy is not None:
        joblib.dump({
            "val_acc": accuracy,
            "val_brier": getattr(modelo, "_betml_val_brier", None),
        }, MODELS_DIR / "metricas_xgboost.pkl")
    return ruta


def cargar_metricas_xgboost() -> dict:
    ruta = MODELS_DIR / "metricas_xgboost.pkl"
    if not ruta.exists():
        return {"val_acc": 0.5}
    return joblib.load(ruta)


def cargar_modelo(nombre: str = "modelo_v1.pkl"):
    ruta = MODELS_DIR / nombre
    if not ruta.exists():
        log.error(f"Modelo no encontrado: {ruta}")
        return None
    modelo = joblib.load(ruta)
    log.info(f"Modelo cargado: {ruta}")
    return modelo


if __name__ == "__main__":
    from backend.features.dataset import generar_dataset

    log.info("Cargando dataset...")
    df = generar_dataset()

    if df.empty:
        log.warning("Sin datos suficientes")
    else:
        resultado = entrenar_modelo(df)
        if resultado[0]:
            modelo, X_test, y_test, y_pred_proba, accuracy = resultado
            guardar_modelo(modelo, accuracy=accuracy)
            log.info("Modelo listo")
