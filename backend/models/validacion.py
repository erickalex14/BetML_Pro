"""Evaluación de modelos respetando el orden real de los partidos."""
import pandas as pd
import numpy as np


def brier_confianza_elegida(y_real, probabilidades) -> float:
    """Brier binario de la clase elegida: confianza vs acertó/falló."""
    y = np.asarray(y_real, dtype=int)
    proba = np.asarray(probabilidades, dtype=float)
    elegida = proba.argmax(axis=1)
    confianza = proba.max(axis=1)
    acerto = (elegida == y).astype(float)
    return float(np.mean((confianza - acerto) ** 2))


def division_temporal(df: pd.DataFrame, proporcion_validacion: float = 0.20,
                       columna_fecha: str = "fecha") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Reserva el bloque cronológico reciente sin partir un mismo día."""
    if columna_fecha not in df.columns:
        raise ValueError(f"El dataset necesita la columna {columna_fecha!r}")
    if not 0 < proporcion_validacion < 1:
        raise ValueError("proporcion_validacion debe estar entre 0 y 1")
    if len(df) < 10:
        raise ValueError("Se necesitan al menos 10 partidos para validación temporal")

    ordenado = df.copy()
    ordenado[columna_fecha] = pd.to_datetime(ordenado[columna_fecha], errors="coerce")
    if ordenado[columna_fecha].isna().any():
        raise ValueError("Hay partidos sin fecha válida")
    ordenado = ordenado.sort_values([columna_fecha, "partido_id"], kind="stable")
    ordenado["_dia_validacion"] = ordenado[columna_fecha].dt.normalize()

    indice = min(len(ordenado) - 1, int(len(ordenado) * (1 - proporcion_validacion)))
    fecha_corte = ordenado.iloc[indice]["_dia_validacion"]
    entrenamiento = ordenado[ordenado["_dia_validacion"] < fecha_corte].copy()
    validacion = ordenado[ordenado["_dia_validacion"] >= fecha_corte].copy()
    if entrenamiento.empty or validacion.empty:
        raise ValueError("No hay fechas suficientes para separar train y validación")
    if entrenamiento[columna_fecha].max() >= validacion[columna_fecha].min():
        raise AssertionError("La división temporal produjo fechas solapadas")
    return (entrenamiento.drop(columns="_dia_validacion"),
            validacion.drop(columns="_dia_validacion"))


def ventanas_walk_forward(df: pd.DataFrame, n_ventanas: int = 4,
                           proporcion_min_train: float = 0.50,
                           columna_fecha: str = "fecha") -> list[tuple[pd.DataFrame, pd.DataFrame]]:
    """Genera ventanas expansivas; cada validación ocurre después del train."""
    if n_ventanas < 2:
        raise ValueError("n_ventanas debe ser al menos 2")
    if not 0 < proporcion_min_train < 1:
        raise ValueError("proporcion_min_train debe estar entre 0 y 1")
    if columna_fecha not in df.columns:
        raise ValueError(f"El dataset necesita la columna {columna_fecha!r}")

    ordenado = df.copy()
    ordenado[columna_fecha] = pd.to_datetime(ordenado[columna_fecha], errors="coerce")
    if ordenado[columna_fecha].isna().any():
        raise ValueError("Hay partidos sin fecha válida")
    ordenado = ordenado.sort_values([columna_fecha, "partido_id"], kind="stable")
    ordenado["_dia_validacion"] = ordenado[columna_fecha].dt.normalize()
    fechas = list(ordenado["_dia_validacion"].drop_duplicates())
    inicio_validacion = int(len(fechas) * proporcion_min_train)
    fechas_validacion = fechas[inicio_validacion:]
    if inicio_validacion < 1 or len(fechas_validacion) < n_ventanas:
        raise ValueError("No hay fechas suficientes para las ventanas solicitadas")

    base, extra = divmod(len(fechas_validacion), n_ventanas)
    ventanas, cursor = [], 0
    for i in range(n_ventanas):
        tamano = base + (1 if i < extra else 0)
        bloque = fechas_validacion[cursor:cursor + tamano]
        cursor += tamano
        fecha_desde, fecha_hasta = bloque[0], bloque[-1]
        train = ordenado[ordenado["_dia_validacion"] < fecha_desde].copy()
        val = ordenado[
            (ordenado["_dia_validacion"] >= fecha_desde) &
            (ordenado["_dia_validacion"] <= fecha_hasta)
        ].copy()
        if train.empty or val.empty or train[columna_fecha].max() >= val[columna_fecha].min():
            raise AssertionError("Ventana walk-forward inválida")
        ventanas.append((train.drop(columns="_dia_validacion"),
                          val.drop(columns="_dia_validacion")))
    return ventanas
