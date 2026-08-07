"""Calibración de probabilidades del modelo — necesaria para que Kelly
tenga sentido matemático.

XGBoost (como casi todo gradient boosting) no da probabilidades bien
calibradas: cuando dice "90% de confianza" en la práctica acierta menos
de eso. Kelly usa la probabilidad del modelo tal cual para calcular el
edge — si esa probabilidad está inflada, Kelly sobreestima el edge y
apuesta más de lo que debería.

Ajusta una regresión isotónica por clase (one-vs-rest, estándar de
scikit-learn) sobre el set de validación: mapea "probabilidad cruda del
modelo" -> "frecuencia real de acierto observada". También guarda la
densidad de muestras por decil de probabilidad, usada como proxy de
confianza — un rango con pocas muestras en validación es una calibración
menos confiable, aunque la curva diga lo que diga.
"""
import logging
import numpy as np
import joblib
from pathlib import Path
from sklearn.isotonic import IsotonicRegression

log = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent.parent.parent
CALIB_PATH = ROOT_DIR / "data" / "models" / "calibracion.pkl"

N_CLASES = 3  # local, empate, visitante


def ajustar_calibracion(y_test: np.ndarray, y_pred_proba: np.ndarray) -> dict:
    calibradores = {}
    conteos = {}

    for clase in range(N_CLASES):
        y_bin = (np.asarray(y_test) == clase).astype(int)
        p_clase = y_pred_proba[:, clase]

        iso = IsotonicRegression(out_of_bounds="clip", y_min=0.001, y_max=0.999)
        iso.fit(p_clase, y_bin)
        calibradores[clase] = iso

        deciles = np.linspace(0, 1, 11)
        conteo_bucket, _ = np.histogram(p_clase, bins=deciles)
        conteos[clase] = {
            "deciles": deciles,
            "conteos": conteo_bucket,
            "total": len(p_clase),
        }

    return {"calibradores": calibradores, "conteos": conteos}


def calibrar_probabilidades(calibracion: dict, proba_cruda: np.ndarray) -> np.ndarray:
    """Aplica el calibrador de cada clase y renormaliza a que sume 1."""
    calibrados = np.array([
        calibracion["calibradores"][c].predict([proba_cruda[c]])[0]
        for c in range(len(proba_cruda))
    ])
    total = calibrados.sum()
    if total <= 0:
        return proba_cruda  # fallback defensivo, no debería pasar
    return calibrados / total


def factor_confianza(calibracion: dict, clase: int, proba: float) -> float:
    """Cuánto confiar en la calibración de esta clase en este rango de
    probabilidad, según cuántas muestras de validación cayeron ahí.
    1.0 = bucket con densidad normal o mayor. Clip inferior en 0.4 —
    poca data no debería anular Kelly del todo, solo hacerlo más chico."""
    info = calibracion["conteos"][clase]
    deciles = info["deciles"]
    idx = np.searchsorted(deciles, proba, side="right") - 1
    idx = int(np.clip(idx, 0, len(info["conteos"]) - 1))

    conteo_bucket = info["conteos"][idx]
    promedio_esperado = info["total"] / 10  # si los deciles fueran uniformes
    if promedio_esperado <= 0:
        return 0.4

    ratio = conteo_bucket / promedio_esperado
    return float(np.clip(ratio, 0.4, 1.0))


def guardar_calibracion(calibracion: dict, ruta: Path = CALIB_PATH):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(calibracion, ruta)
    log.info(f"Calibración guardada: {ruta}")


def cargar_calibracion(ruta: Path = CALIB_PATH):
    if not ruta.exists():
        log.warning(f"No hay calibración guardada en {ruta}")
        return None
    return joblib.load(ruta)
