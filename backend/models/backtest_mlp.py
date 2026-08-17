"""Walk-forward bajo demanda para la cabeza 1X2 del MLP."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from backend.features.dataset import FEATURES_ML, TARGET
from backend.models.backtest_walk_forward import _metricas
from backend.models.mlp import entrenar_mlp
from backend.models.validacion import ventanas_walk_forward

ROOT_DIR = Path(__file__).parent.parent.parent
SALIDA_DEFAULT = ROOT_DIR / "data" / "backtests" / "mlp_walk_forward.json"


def _predecir(resultado: dict, df: pd.DataFrame) -> np.ndarray:
    x = resultado["scaler_x"].transform(
        df[FEATURES_ML].fillna(0).to_numpy(dtype=np.float32))
    resultado["modelo"].eval()
    with torch.no_grad():
        logits = resultado["modelo"](torch.tensor(x, dtype=torch.float32))["1x2"]
    return torch.softmax(logits, dim=1).numpy()


def evaluar_mlp(df: pd.DataFrame, n_ventanas: int = 4, epochs: int = 30,
                n_hilos: int = 2, periodo_desde=None, periodo_hasta=None) -> dict:
    torch.set_num_threads(n_hilos)
    ventanas_out, ys, probas, bases, fechas = [], [], [], [], []
    for numero, (train, val) in enumerate(ventanas_walk_forward(df, n_ventanas), 1):
        torch.manual_seed(42 + numero)
        np.random.seed(42 + numero)
        resultado = entrenar_mlp(
            train, epochs=epochs, patience=5, df_val=val)
        y = val[TARGET].to_numpy(dtype=int)
        proba = _predecir(resultado, val)
        frecuencias = (
            train[TARGET].value_counts(normalize=True).reindex([0, 1, 2], fill_value=0).to_numpy()
        )
        base = np.tile(frecuencias, (len(val), 1))
        ventanas_out.append({
            "ventana": numero,
            "train_n": int(len(train)),
            "validacion_n": int(len(val)),
            "validacion_desde": val["fecha"].min().isoformat(),
            "validacion_hasta": val["fecha"].max().isoformat(),
            **_metricas(y, proba),
        })
        ys.append(y)
        probas.append(proba)
        bases.append(base)
        fechas.append(pd.to_datetime(val["fecha"]).to_numpy())

    y = np.concatenate(ys)
    proba = np.vstack(probas)
    base = np.vstack(bases)
    fechas = pd.to_datetime(np.concatenate(fechas))
    global_modelo, global_base = _metricas(y, proba), _metricas(y, base)
    reporte = {
        "generado_en": datetime.now(timezone.utc).isoformat(),
        "modelo": "mlp_1x2",
        "metodo": "expanding_window",
        "global": global_modelo,
        "baseline_frecuencias_train": global_base,
        "mejora_vs_baseline": {
            "accuracy": round(global_modelo["accuracy"] - global_base["accuracy"], 6),
            "log_loss": round(global_base["log_loss"] - global_modelo["log_loss"], 6),
            "brier_multiclase": round(
                global_base["brier_multiclase"] - global_modelo["brier_multiclase"], 6),
        },
        "ventanas": ventanas_out,
        "roi": None,
        "nota_roi": "No calculado: falta snapshot de cuota al emitir.",
    }
    if periodo_desde and periodo_hasta:
        desde, hasta = pd.Timestamp(periodo_desde), pd.Timestamp(periodo_hasta)
        mascara = (fechas >= desde) & (fechas < hasta)
        reporte["periodo_solicitado"] = {
            "desde": desde.isoformat(), "hasta_exclusivo": hasta.isoformat(),
            "metricas": _metricas(y[mascara], proba[mascara]) if mascara.any() else None,
        }
    return reporte


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--ventanas", type=int, default=4)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--n-hilos", type=int, default=2)
    parser.add_argument("--desde")
    parser.add_argument("--hasta")
    parser.add_argument("--salida", type=Path, default=SALIDA_DEFAULT)
    args = parser.parse_args()
    if bool(args.desde) != bool(args.hasta):
        parser.error("--desde y --hasta deben usarse juntos")
    reporte = evaluar_mlp(
        pd.read_pickle(args.dataset), args.ventanas, args.epochs,
        args.n_hilos, args.desde, args.hasta)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(reporte, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(reporte["global"], ensure_ascii=False))
    print(f"Reporte: {args.salida}")


if __name__ == "__main__":
    main()
