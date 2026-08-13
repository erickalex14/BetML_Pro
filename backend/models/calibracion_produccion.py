"""El sistema aprende de sus propios errores, por tipo de mercado.

La idea, en criollo: si venimos diciendo "córners over 64%" y en la
cancha eso pasa el 10% de las veces, la próxima vez hay que declarar
menos. Esto lo mide y lo corrige solo.

Por qué esto y no "reentrenar con las predicciones": el reentreno
aprende de los PARTIDOS terminados, y el resultado del partido ya es la
etiqueta — anotar aparte "predijimos 64%" no agrega información sobre
ese partido. Lo que sí agrega, y no se puede sacar del dataset, es la
comparación entre lo declarado y lo ocurrido: eso mide si el número que
le pasamos a Kelly es confiable. Y ahí se juega la plata: con una
probabilidad inflada, Kelly recomienda apostar de más.

Medición real del 2026-08-13 (43 predicciones cerradas):
    corners    declarado 64%  ->  real 10%   (-54 pp)
    handicap   declarado 42%  ->  real  0%   (-42 pp)
    btts       declarado 64%  ->  real 25%   (-39 pp)
    goles      declarado 54%  ->  real 43%   (-11 pp)
    1X2        declarado 26%  ->  real 33%   (+8 pp, iba pesimista)

Tres decisiones de diseño, todas por el mismo motivo (poca muestra):

1. **Por familia de mercado, no global.** El error de córners no dice
   nada del 1X2; promediarlos escondería ambos.
2. **Encogimiento hacia 1.** Con 10 muestras, la frecuencia observada es
   ruidosa. El factor se mezcla con "no corregir nada", pesando por
   cuántas muestras hay: con pocas casi no corrige, con muchas manda lo
   observado.
3. **Ventana móvil.** Solo se miran las últimas N cerradas de cada
   familia. Importa porque los errores viejos pueden venir de un bug ya
   arreglado — el desastre de córners salía de un lambda mal calculado,
   corregido ese mismo día. Sin ventana, el sistema seguiría castigando
   para siempre un problema que ya no existe.
"""
import logging
from collections import defaultdict
from pathlib import Path

import joblib

log = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent.parent.parent
RUTA = ROOT_DIR / "data" / "models" / "calibracion_produccion.pkl"

# Mínimo por familia para tocar algo. Por debajo, no corrige.
MIN_MUESTRAS = 8
# Fuerza del encogimiento: equivale a "k observaciones virtuales que
# dicen que el modelo estaba bien". Con n=k el factor va a mitad de
# camino entre no corregir y corregir del todo.
K_ENCOGIMIENTO = 20
# Cuántas cerradas por familia se miran (las más recientes)
VENTANA = 200
# Topes de seguridad: ni anular una probabilidad ni inflarla
FACTOR_MIN, FACTOR_MAX = 0.5, 1.3


def familia_de(mercado: str) -> str:
    """Agrupa las claves de mercado en familias que comparten mecánica.
    Mismo vocabulario que las claves de kelly.py."""
    m = mercado or ""
    if m.startswith("corners"):
        return "corners"
    if m.startswith("tarjetas"):
        return "tarjetas"
    if m.startswith("rojas"):
        return "rojas"
    if m.startswith("goles_equipo"):
        return "goles_equipo"
    if m.startswith("goles"):
        return "goles"
    if m.startswith("btts"):
        return "btts"
    if m.startswith("handicap"):
        return "handicap"
    if m in ("local", "empate", "visitante"):
        return "1x2"
    return "otros"


def ajustar_desde_predicciones(db, guardar: bool = True) -> dict:
    """Calcula un factor de corrección por familia de mercado."""
    from backend.db.modelos import Prediccion

    filas = (
        db.query(Prediccion)
        .filter(Prediccion.acerto.isnot(None), Prediccion.probabilidad.isnot(None))
        .order_by(Prediccion.creado_en.desc())
        .limit(VENTANA * 8)
        .all()
    )

    por_familia = defaultdict(list)
    for p in filas:
        fam = familia_de(p.mercado)
        if len(por_familia[fam]) < VENTANA:
            por_familia[fam].append((p.probabilidad, 1 if p.acerto else 0))

    factores = {}
    for fam, datos in por_familia.items():
        n = len(datos)
        if n < MIN_MUESTRAS:
            continue
        declarado = sum(d[0] for d in datos) / n
        real = sum(d[1] for d in datos) / n
        if declarado <= 0:
            continue

        # Encogido hacia 1 según cuánta muestra hay: es
        # (n*real + k*declarado) / ((n+k)*declarado)
        factor = (n * real + K_ENCOGIMIENTO * declarado) / ((n + K_ENCOGIMIENTO) * declarado)
        factor = max(FACTOR_MIN, min(FACTOR_MAX, factor))

        factores[fam] = {
            "factor": round(factor, 4),
            "n": n,
            "declarado": round(declarado, 4),
            "real": round(real, 4),
        }
        log.info(f"Calibración {fam}: declarado {declarado:.0%} vs real {real:.0%} "
                 f"(n={n}) -> factor {factor:.3f}")

    if not factores:
        log.info(f"Calibración de producción: ninguna familia llega a "
                 f"{MIN_MUESTRAS} predicciones cerradas todavía")

    if guardar and factores:
        RUTA.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(factores, RUTA)

    return factores


def cargar() -> dict:
    if not RUTA.exists():
        return {}
    try:
        return joblib.load(RUTA)
    except Exception as e:  # archivo corrupto: no romper la API por esto
        log.warning(f"No se pudo cargar la calibración de producción: {e}")
        return {}


def corregir(probabilidad: float, mercado: str, factores: dict | None = None) -> float:
    """Aplica lo aprendido. Sin datos de esa familia devuelve la
    probabilidad tal cual — nunca inventa una corrección."""
    if factores is None:
        factores = cargar()
    datos = factores.get(familia_de(mercado)) if factores else None
    if not datos:
        return probabilidad
    return max(0.0, min(1.0, probabilidad * datos["factor"]))
