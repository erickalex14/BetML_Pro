import logging
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
from xgboost import XGBClassifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

ROOT_DIR   = Path(__file__).parent.parent.parent
MODELS_DIR = ROOT_DIR / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Features que usa el modelo — exactamente las que
# calcula calculador.py. El orden importa.
FEATURES = [
    "forma_local_puntos",
    "forma_local_gf",
    "forma_local_gc",
    "forma_visit_puntos",
    "forma_visit_gf",
    "forma_visit_gc",
    "win_rate_local",
    "win_rate_visit",
    "h2h_wins_local",
    "h2h_empates",
    "h2h_wins_visit",
    "h2h_goles_local",
    "h2h_goles_visit",
]

TARGET = "resultado"


def entrenar_modelo(df: pd.DataFrame) -> XGBClassifier:
    """
    Entrena el modelo XGBoost con el dataset de features.
    Configurado para aprovechar múltiples cores del servidor.

    El modelo predice resultado:
      0 = local gana
      1 = empate
      2 = visitante gana
    """
    log.info("=" * 55)
    log.info("  Entrenando modelo XGBoost — BetML Pro")
    log.info("=" * 55)

    if df.empty:
        log.error("Dataset vacío — no hay datos para entrenar")
        return None

    log.info(f"Dataset: {df.shape[0]} partidos, {len(FEATURES)} features")

    # Separa features (X) y target (y)
    # Es como separar las columnas de entrada de la columna
    # que queremos predecir
    X = df[FEATURES].fillna(0)   # fillna por si hay valores nulos
    y = df[TARGET]

    log.info(f"Distribución del target:")
    log.info(f"  Local gana  (0): {(y==0).sum()} ({(y==0).mean()*100:.1f}%)")
    log.info(f"  Empate      (1): {(y==1).sum()} ({(y==1).mean()*100:.1f}%)")
    log.info(f"  Visit gana  (2): {(y==2).sum()} ({(y==2).mean()*100:.1f}%)")

    # Split 80% entrenamiento / 20% test
    # stratify=y asegura que la distribución de clases
    # sea igual en train y test — importante para clases desbalanceadas
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    log.info(f"Train: {len(X_train)} partidos | Test: {len(X_test)} partidos")

    # Configuración XGBoost optimizada para tu servidor
    # n_jobs=-1 → usa TODOS los cores disponibles (ambos Xeons)
    # tree_method='hist' → el más eficiente para datasets grandes
    modelo = XGBClassifier(
        n_estimators=500,        # número de árboles
        max_depth=6,             # profundidad máxima de cada árbol
        learning_rate=0.05,      # qué tan rápido aprende
        subsample=0.8,           # % de datos por árbol (evita overfitting)
        colsample_bytree=0.8,    # % de features por árbol
        min_child_weight=3,      # mínimo de muestras por hoja
        gamma=0.1,               # regularización
        reg_alpha=0.1,           # regularización L1
        reg_lambda=1.0,          # regularización L2
        n_jobs=-1,               # TODOS los cores del servidor
        tree_method="hist",      # más eficiente en RAM grande
        device="cpu",            # CPU (los Xeons)
        random_state=42,
        eval_metric="mlogloss",  # métrica para multiclase
        early_stopping_rounds=30 # para si el modelo deja de mejorar
    )

    log.info("Entrenando... (esto puede tardar unos minutos)")

    # Entrena con validación en cada iteración
    # eval_set permite ver el progreso del entrenamiento
    modelo.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=50   # muestra progreso cada 50 árboles
    )

    # ── Evaluación ─────────────────────────────────────────
    y_pred       = modelo.predict(X_test)
    y_pred_proba = modelo.predict_proba(X_test)

    accuracy = accuracy_score(y_test, y_pred)

    log.info("\n" + "=" * 55)
    log.info(f"  RESULTADOS DEL MODELO")
    log.info("=" * 55)
    log.info(f"  Accuracy general: {accuracy*100:.2f}%")
    log.info(f"  Benchmark random: 33.33%")
    log.info(f"  Mejora vs random: +{(accuracy-0.333)*100:.2f}%")
    log.info("\n" + classification_report(
        y_test, y_pred,
        target_names=["Local", "Empate", "Visitante"]
    ))

    # ── Importancia de features ─────────────────────────────
    importancias = pd.Series(
        modelo.feature_importances_,
        index=FEATURES
    ).sort_values(ascending=False)

    log.info("  Features más importantes:")
    for feat, imp in importancias.head(5).items():
        log.info(f"    {feat:<30} {imp:.4f}")

    return modelo, X_test, y_test, y_pred_proba


def guardar_modelo(modelo: XGBClassifier, nombre: str = "modelo_v1.pkl"):
    """
    Guarda el modelo entrenado en disco usando joblib.
    joblib es más eficiente que pickle para modelos grandes.
    """
    ruta = MODELS_DIR / nombre
    joblib.dump(modelo, ruta)
    log.info(f"Modelo guardado en: {ruta}")
    return ruta


def cargar_modelo(nombre: str = "modelo_v1.pkl") -> XGBClassifier:
    """
    Carga el modelo desde disco.
    Se usa en producción para hacer predicciones sin re-entrenar.
    """
    ruta = MODELS_DIR / nombre
    if not ruta.exists():
        log.error(f"Modelo no encontrado: {ruta}")
        return None
    modelo = joblib.load(ruta)
    log.info(f"Modelo cargado desde: {ruta}")
    return modelo


if __name__ == "__main__":
    from backend.features.dataset import generar_dataset

    log.info("Cargando dataset...")
    df = generar_dataset(temporadas=[2023, 2024])

    if df.empty:
        log.warning("Sin datos — espera agosto para entrenar con datos reales")
    else:
        resultado = entrenar_modelo(df)
        if resultado:
            modelo, X_test, y_test, y_pred_proba = resultado
            guardar_modelo(modelo)
            log.info("Modelo listo para predicciones")