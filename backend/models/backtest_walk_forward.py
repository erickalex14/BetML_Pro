"""Backtest cronológico XGBoost ejecutable bajo demanda, nunca por scheduler."""
import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, log_loss
from sklearn.utils.class_weight import compute_sample_weight

from backend.features.dataset import FEATURES_ML, TARGET, generar_dataset
from backend.models.entrenador import crear_clasificador_xgboost
from backend.models.validacion import ventanas_walk_forward

log = logging.getLogger(__name__)
ROOT_DIR = Path(__file__).parent.parent.parent
SALIDA_DEFAULT = ROOT_DIR / "data" / "backtests" / "xgboost_walk_forward.json"


def _metricas(y: np.ndarray, proba: np.ndarray) -> dict:
    pred = proba.argmax(axis=1)
    one_hot = np.eye(3)[y.astype(int)]
    confianza = proba.max(axis=1)
    altas = confianza >= 0.65
    acierto = pred == y
    return {
        "n": int(len(y)),
        "accuracy": round(float(accuracy_score(y, pred)), 6),
        "log_loss": round(float(log_loss(y, proba, labels=[0, 1, 2])), 6),
        "brier_multiclase": round(float(np.mean(np.sum((proba - one_hot) ** 2, axis=1))), 6),
        "confianza_media": round(float(confianza.mean()), 6),
        "gap_calibracion": round(float(acierto.mean() - confianza.mean()), 6),
        "alta_confianza": {
            "umbral": 0.65,
            "n": int(altas.sum()),
            "cobertura": round(float(altas.mean()), 6),
            "accuracy": round(float(acierto[altas].mean()), 6) if altas.any() else None,
            "confianza_media": round(float(confianza[altas].mean()), 6) if altas.any() else None,
        },
    }


def evaluar_walk_forward(df, n_ventanas: int = 4, n_jobs: int = 2,
                         periodo_desde=None, periodo_hasta=None) -> dict:
    resultados, ys, probas, probas_baseline, fechas = [], [], [], [], []
    for numero, (train, val) in enumerate(
            ventanas_walk_forward(df, n_ventanas=n_ventanas), start=1):
        modelo = crear_clasificador_xgboost(n_jobs=n_jobs)
        x_train = train[FEATURES_ML].fillna(0)
        y_train = train[TARGET]
        x_val = val[FEATURES_ML].fillna(0)
        y_val = val[TARGET].to_numpy(dtype=int)
        pesos = compute_sample_weight(class_weight="balanced", y=y_train)
        modelo.fit(
            x_train, y_train,
            sample_weight=pesos,
            eval_set=[(x_val, y_val)],
            verbose=False,
        )
        proba = modelo.predict_proba(x_val)
        frecuencias = (
            y_train.value_counts(normalize=True).reindex([0, 1, 2], fill_value=0).to_numpy()
        )
        proba_baseline = np.tile(frecuencias, (len(y_val), 1))
        metricas_modelo = _metricas(y_val, proba)
        metricas_baseline = _metricas(y_val, proba_baseline)
        resultados.append({
            "ventana": numero,
            "train_n": int(len(train)),
            "train_hasta": train["fecha"].max().isoformat(),
            "validacion_desde": val["fecha"].min().isoformat(),
            "validacion_hasta": val["fecha"].max().isoformat(),
            **metricas_modelo,
            "baseline_frecuencias_train": metricas_baseline,
        })
        ys.append(y_val)
        probas.append(proba)
        probas_baseline.append(proba_baseline)
        fechas.append(pd.to_datetime(val["fecha"]).to_numpy())
        log.info("Ventana %s/%s terminada", numero, n_ventanas)

    y_global = np.concatenate(ys)
    proba_global = np.vstack(probas)
    baseline_global = np.vstack(probas_baseline)
    fecha_global = pd.to_datetime(np.concatenate(fechas))
    reporte = {
        "generado_en": datetime.now(timezone.utc).isoformat(),
        "modelo": "xgboost",
        "metodo": "expanding_window",
        "ventanas": resultados,
        "global": _metricas(y_global, proba_global),
        "baseline_frecuencias_train": _metricas(y_global, baseline_global),
        "roi": None,
        "nota_roi": "No calculado: la base no conserva la cuota exacta al emitir cada predicción.",
    }
    reporte["mejora_vs_baseline"] = {
        "accuracy": round(
            reporte["global"]["accuracy"] - reporte["baseline_frecuencias_train"]["accuracy"], 6),
        "log_loss": round(
            reporte["baseline_frecuencias_train"]["log_loss"] - reporte["global"]["log_loss"], 6),
        "brier_multiclase": round(
            reporte["baseline_frecuencias_train"]["brier_multiclase"] -
            reporte["global"]["brier_multiclase"], 6),
    }
    if periodo_desde is not None and periodo_hasta is not None:
        desde, hasta = pd.Timestamp(periodo_desde), pd.Timestamp(periodo_hasta)
        mascara = (fecha_global >= desde) & (fecha_global < hasta)
        reporte["periodo_solicitado"] = {
            "desde": desde.isoformat(),
            "hasta_exclusivo": hasta.isoformat(),
            "metricas": _metricas(y_global[mascara], proba_global[mascara])
            if mascara.any() else None,
        }
    return reporte


def guardar_reporte(reporte: dict, ruta: Path = SALIDA_DEFAULT) -> Path:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(reporte, indent=2, ensure_ascii=False), encoding="utf-8")
    return ruta


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ventanas", type=int, default=4)
    parser.add_argument("--n-jobs", type=int, default=2)
    parser.add_argument("--usar-cache", action="store_true",
                        help="Usa el dataset local existente; útil para validar el auditor sin consultar BD")
    parser.add_argument("--dataset", type=Path,
                        help="Archivo .pkl explícito; no consulta la base ni altera el caché")
    parser.add_argument("--desde", help="Inicio inclusivo del período adicional, ISO-8601")
    parser.add_argument("--hasta", help="Fin exclusivo del período adicional, ISO-8601")
    parser.add_argument("--salida", type=Path, default=SALIDA_DEFAULT)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    df = pd.read_pickle(args.dataset) if args.dataset else generar_dataset(usar_cache=args.usar_cache)
    if bool(args.desde) != bool(args.hasta):
        parser.error("--desde y --hasta deben usarse juntos")
    reporte = evaluar_walk_forward(
        df, args.ventanas, args.n_jobs, args.desde, args.hasta)
    ruta = guardar_reporte(reporte, args.salida)
    print(json.dumps(reporte["global"], ensure_ascii=False))
    print(f"Reporte: {ruta}")


if __name__ == "__main__":
    main()
