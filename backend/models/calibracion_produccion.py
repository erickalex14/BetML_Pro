"""Calibración medida en PRODUCCIÓN — con las predicciones que ya se
cerraron contra el resultado real (acertada/fallada).

Por qué existe, además de calibracion.py: esa se ajusta sobre el split
de test del entrenamiento (ver entrenador.py), o sea sobre partidos
históricos con las features calculadas hacia atrás. Esta se ajusta con
lo que el sistema realmente dijo antes de cada partido y lo que
realmente pasó después. Es la única señal que NO se puede sacar del
dataset: mide si cuando decimos "72%" acierta ~72 de cada 100, o si en
la cancha ese 72% resulta ser 55%.

Ojo con qué NO es esto: no reentrena el clasificador. Un partido
terminado ya entra al dataset del reentreno diario con o sin
predicciones guardadas — el resultado del partido ES la etiqueta. Lo
que agregan las predicciones cerradas es la comparación entre
probabilidad declarada y frecuencia observada, que es justo lo que
importa para apostar (una probabilidad inflada arruina el cálculo de
Kelly aunque el modelo acierte "el ganador" seguido).
"""
import logging
from pathlib import Path

import joblib
import numpy as np
from sklearn.isotonic import IsotonicRegression

log = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent.parent.parent
RUTA = ROOT_DIR / "data" / "models" / "calibracion_produccion.pkl"

# Con pocas muestras la curva se sobreajusta al ruido y "corrige" cosas
# que no existen. Por debajo de esto no se guarda nada y el sistema
# sigue con la calibración del entrenamiento, que es el default sano.
MIN_MUESTRAS = 150


def ajustar_desde_predicciones(db, guardar: bool = True) -> dict | None:
    """Ajusta la curva probabilidad-declarada -> frecuencia-real sobre
    las predicciones ya cerradas. None si todavía no hay suficientes."""
    from backend.db.modelos import Prediccion

    filas = (
        db.query(Prediccion.probabilidad, Prediccion.acerto)
        .filter(Prediccion.acerto.isnot(None), Prediccion.probabilidad.isnot(None))
        .all()
    )
    if len(filas) < MIN_MUESTRAS:
        log.info(f"Calibración de producción: {len(filas)} predicciones cerradas, "
                 f"hacen falta {MIN_MUESTRAS} — se mantiene la del entrenamiento")
        return None

    probs = np.array([f[0] for f in filas], dtype=float)
    aciertos = np.array([1 if f[1] else 0 for f in filas], dtype=int)

    iso = IsotonicRegression(out_of_bounds="clip", y_min=0.001, y_max=0.999)
    iso.fit(probs, aciertos)

    resultado = {
        "curva": iso,
        "n_muestras": len(filas),
        "prob_media_declarada": float(probs.mean()),
        "acierto_real": float(aciertos.mean()),
    }

    log.info(f"Calibración de producción ajustada con {len(filas)} predicciones — "
             f"probabilidad media declarada {probs.mean():.3f} vs acierto real "
             f"{aciertos.mean():.3f}")

    if guardar:
        RUTA.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(resultado, RUTA)

    return resultado


def cargar() -> dict | None:
    if not RUTA.exists():
        return None
    try:
        return joblib.load(RUTA)
    except Exception as e:  # archivo corrupto/incompatible: no romper la API por esto
        log.warning(f"No se pudo cargar la calibración de producción: {e}")
        return None


def probabilidad_realista(prob_declarada: float, calibracion: dict | None = None) -> float:
    """Corrige una probabilidad con lo observado en producción. Sin datos
    suficientes devuelve la original — nunca inventa una corrección."""
    if calibracion is None:
        calibracion = cargar()
    if not calibracion or "curva" not in calibracion:
        return prob_declarada
    return float(calibracion["curva"].predict([prob_declarada])[0])
