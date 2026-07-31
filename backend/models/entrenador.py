import logging
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import accuracy_score, classification_report
from xgboost import XGBClassifier
from backend.features.dataset import FEATURES_ML, TARGET

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

ROOT_DIR   = Path(__file__).parent.parent.parent
MODELS_DIR = ROOT_DIR / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def entrenar_modelo(df: pd.DataFrame) -> tuple:
    log.info("=" * 55)
    log.info("  Entrenando modelo XGBoost — BetML Pro")
    log.info("=" * 55)

    if df.empty:
        log.error("Dataset vacío")
        return None, None, None, None

    log.info(f"Dataset: {df.shape[0]} partidos, {len(FEATURES_ML)} features")

    X = df[FEATURES_ML].fillna(0)
    y = df[TARGET]

    log.info(f"Distribución target:")
    log.info(f"  Local gana  (0): {(y==0).sum()} ({(y==0).mean()*100:.1f}%)")
    log.info(f"  Empate      (1): {(y==1).sum()} ({(y==1).mean()*100:.1f}%)")
    log.info(f"  Visit gana  (2): {(y==2).sum()} ({(y==2).mean()*100:.1f}%)")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    log.info(f"Train: {len(X_train)} | Test: {len(X_test)}")

    # XGBoost optimizado para el servidor
    # n_jobs=-1 usa todos los núcleos disponibles
    modelo = XGBClassifier(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.0,
        n_jobs=-1,
        tree_method="hist",
        device="cpu",
        random_state=42,
        eval_metric="mlogloss",
        early_stopping_rounds=30
    )

    log.info("Entrenando XGBoost...")

    modelo.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=100
    )

    # Evaluación
    y_pred       = modelo.predict(X_test)
    y_pred_proba = modelo.predict_proba(X_test)
    accuracy     = accuracy_score(y_test, y_pred)

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

    return modelo, X_test, y_test, y_pred_proba


def guardar_modelo(modelo: XGBClassifier,
                   nombre: str = "modelo_v1.pkl"):
    ruta = MODELS_DIR / nombre
    joblib.dump(modelo, ruta)
    log.info(f"Modelo guardado: {ruta}")
    return ruta


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
    df = generar_dataset(temporadas=[2023, 2024])

    if df.empty:
        log.warning("Sin datos suficientes")
    else:
        resultado = entrenar_modelo(df)
        if resultado[0]:
            modelo, X_test, y_test, y_pred_proba = resultado
            guardar_modelo(modelo)
            log.info("Modelo listo")