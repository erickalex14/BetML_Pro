"""Red neuronal MLP multiobjetivo — predice 1X2, Over/Under 2.5, BTTS,
corners y tarjetas esperados, y resultado al medio tiempo, en una sola
pasada. Compartir el tronco entre mercados deja que el modelo use señal
de un mercado para mejorar otro (xG alto empuja Over2.5 Y favorece al
local — es la misma información vista desde ángulos distintos).

Arquitectura: 29 features -> 256 -> 128 -> 64 (ReLU, BatchNorm, Dropout
0.3 entre capas) -> 6 cabezas de salida.

Corners y tarjetas se modelan como REGRESIÓN (total esperado), no como
un umbral over/under fijo — así el número sale directo como λ para
Monte Carlo, igual que xG, en vez de atarse a una línea específica.

No todos los partidos tienen corners/tarjetas/HT en Sofascore — esas
tres cabezas usan loss enmascarada: las filas sin dato no aportan
gradiente para esa cabeza, pero sí para el resto.
"""
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_class_weight

from backend.features.dataset import FEATURES_ML
from backend.models.validacion import division_temporal, brier_confianza_elegida

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent.parent.parent
MODELS_DIR = ROOT_DIR / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
MLP_PATH = MODELS_DIR / "mlp_v1.pt"


class RedMultiObjetivo(nn.Module):
    def __init__(self, n_features: int, dropout: float = 0.3):
        super().__init__()
        self.tronco = nn.Sequential(
            nn.Linear(n_features, 256), nn.BatchNorm1d(256), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(256, 128), nn.BatchNorm1d(128), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(128, 64), nn.BatchNorm1d(64), nn.ReLU(), nn.Dropout(dropout),
        )
        self.head_1x2      = nn.Linear(64, 3)
        self.head_over25   = nn.Linear(64, 1)
        self.head_btts     = nn.Linear(64, 1)
        self.head_corners  = nn.Linear(64, 1)
        self.head_tarjetas = nn.Linear(64, 1)
        self.head_ht       = nn.Linear(64, 3)

    def forward(self, x):
        z = self.tronco(x)
        return {
            "1x2":      self.head_1x2(z),
            "over25":   self.head_over25(z).squeeze(-1),
            "btts":     self.head_btts(z).squeeze(-1),
            "corners":  self.head_corners(z).squeeze(-1),
            "tarjetas": self.head_tarjetas(z).squeeze(-1),
            "ht":       self.head_ht(z),
        }


class _DatasetMultiObjetivo(Dataset):
    def __init__(self, df: pd.DataFrame, scaler_x: StandardScaler,
                 media_corners: float, std_corners: float,
                 media_tarjetas: float, std_tarjetas: float):
        X = scaler_x.transform(df[FEATURES_ML].fillna(0).to_numpy(dtype=np.float32))
        self.X = torch.tensor(X, dtype=torch.float32)

        goles_total = df["goles_local_ft"] + df["goles_visit_ft"]
        self.y_1x2 = torch.tensor(df["resultado"].to_numpy(), dtype=torch.long)
        self.y_over25 = torch.tensor(
            (goles_total > 2.5).astype(np.float32).to_numpy(), dtype=torch.float32)
        self.y_btts = torch.tensor(
            ((df["goles_local_ft"] > 0) & (df["goles_visit_ft"] > 0))
            .astype(np.float32).to_numpy(), dtype=torch.float32)

        self.mask_corners = torch.tensor(df["corners_total"].notna().to_numpy(), dtype=torch.bool)
        corners_norm = (df["corners_total"].fillna(media_corners) - media_corners) / std_corners
        self.y_corners = torch.tensor(corners_norm.to_numpy(dtype=np.float32), dtype=torch.float32)

        self.mask_tarjetas = torch.tensor(df["amarillas_total"].notna().to_numpy(), dtype=torch.bool)
        tarjetas_norm = (df["amarillas_total"].fillna(media_tarjetas) - media_tarjetas) / std_tarjetas
        self.y_tarjetas = torch.tensor(tarjetas_norm.to_numpy(dtype=np.float32), dtype=torch.float32)

        self.mask_ht = torch.tensor(df["resultado_ht"].notna().to_numpy(), dtype=torch.bool)
        self.y_ht = torch.tensor(df["resultado_ht"].fillna(-1).astype(int).to_numpy(), dtype=torch.long)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return {
            "x": self.X[idx],
            "y_1x2": self.y_1x2[idx],
            "y_over25": self.y_over25[idx],
            "y_btts": self.y_btts[idx],
            "y_corners": self.y_corners[idx], "mask_corners": self.mask_corners[idx],
            "y_tarjetas": self.y_tarjetas[idx], "mask_tarjetas": self.mask_tarjetas[idx],
            "y_ht": self.y_ht[idx], "mask_ht": self.mask_ht[idx],
        }


def _perdida_batch(pred: dict, batch: dict, pesos_clase: torch.Tensor) -> tuple:
    # Empate es ~25% de los partidos — sin pesos balanceados, la cabeza
    # 1X2 aprende que nunca predecirlo ya minimiza la loss (mismo
    # problema que en XGBoost, ver entrenador.py). ht comparte la
    # ponderación por ser la misma estructura de 3 clases.
    ce = nn.CrossEntropyLoss(weight=pesos_clase)
    bce = nn.BCEWithLogitsLoss()
    mse = nn.MSELoss()

    perdidas = {
        "1x2": ce(pred["1x2"], batch["y_1x2"]),
        "over25": bce(pred["over25"], batch["y_over25"]),
        "btts": bce(pred["btts"], batch["y_btts"]),
    }

    m = batch["mask_corners"]
    if m.any():
        perdidas["corners"] = mse(pred["corners"][m], batch["y_corners"][m])

    m = batch["mask_tarjetas"]
    if m.any():
        perdidas["tarjetas"] = mse(pred["tarjetas"][m], batch["y_tarjetas"][m])

    m = batch["mask_ht"]
    if m.any():
        perdidas["ht"] = ce(pred["ht"][m], batch["y_ht"][m])

    total = sum(perdidas.values())
    return total, perdidas


def entrenar_mlp(df: pd.DataFrame, epochs: int = 60, batch_size: int = 128,
                  lr: float = 0.001, patience: int = 8,
                  df_val: pd.DataFrame | None = None) -> dict:
    log.info("=" * 55)
    log.info("  Entrenando MLP multiobjetivo — BetML Pro")
    log.info("=" * 55)

    df_train, df_val = division_temporal(df) if df_val is None else (df, df_val)
    log.info(f"  Corte temporal: train hasta {df_train['fecha'].max()} | "
             f"validación desde {df_val['fecha'].min()}")

    scaler_x = StandardScaler().fit(df_train[FEATURES_ML].fillna(0).to_numpy())

    media_corners = df_train["corners_total"].mean()
    std_corners = df_train["corners_total"].std() or 1.0
    media_tarjetas = df_train["amarillas_total"].mean()
    std_tarjetas = df_train["amarillas_total"].std() or 1.0

    ds_train = _DatasetMultiObjetivo(df_train, scaler_x, media_corners, std_corners,
                                      media_tarjetas, std_tarjetas)
    ds_val = _DatasetMultiObjetivo(df_val, scaler_x, media_corners, std_corners,
                                    media_tarjetas, std_tarjetas)

    dl_train = DataLoader(ds_train, batch_size=batch_size, shuffle=True)
    dl_val = DataLoader(ds_val, batch_size=batch_size, shuffle=False)

    pesos_np = compute_class_weight("balanced", classes=np.array([0, 1, 2]),
                                     y=df_train["resultado"].to_numpy())
    pesos_clase = torch.tensor(pesos_np, dtype=torch.float32)

    modelo = RedMultiObjetivo(n_features=len(FEATURES_ML))
    optim = torch.optim.AdamW(modelo.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optim, mode="min", patience=5, factor=0.5)

    mejor_val_loss = float("inf")
    epochs_sin_mejora = 0
    mejor_estado = None

    for epoch in range(epochs):
        modelo.train()
        loss_train = 0.0
        for batch in dl_train:
            optim.zero_grad()
            pred = modelo(batch["x"])
            loss, _ = _perdida_batch(pred, batch, pesos_clase)
            loss.backward()
            optim.step()
            loss_train += loss.item() * len(batch["x"])
        loss_train /= len(ds_train)

        modelo.eval()
        loss_val = 0.0
        aciertos_1x2 = 0
        with torch.no_grad():
            for batch in dl_val:
                pred = modelo(batch["x"])
                loss, _ = _perdida_batch(pred, batch, pesos_clase)
                loss_val += loss.item() * len(batch["x"])
                aciertos_1x2 += (pred["1x2"].argmax(dim=1) == batch["y_1x2"]).sum().item()
        loss_val /= len(ds_val)
        acc_1x2 = aciertos_1x2 / len(ds_val)

        scheduler.step(loss_val)

        if epoch % 5 == 0 or epoch == epochs - 1:
            log.info(f"  epoch {epoch:>3} | train_loss={loss_train:.4f} "
                      f"val_loss={loss_val:.4f} val_acc_1x2={acc_1x2*100:.2f}%")

        if loss_val < mejor_val_loss:
            mejor_val_loss = loss_val
            mejor_acc_1x2 = acc_1x2
            mejor_estado = {k: v.clone() for k, v in modelo.state_dict().items()}
            epochs_sin_mejora = 0
        else:
            epochs_sin_mejora += 1
            if epochs_sin_mejora >= patience:
                log.info(f"  Early stopping en epoch {epoch} (sin mejora por {patience} epochs)")
                break

    modelo.load_state_dict(mejor_estado)
    probas_val, y_val = [], []
    modelo.eval()
    with torch.no_grad():
        for batch in dl_val:
            salida = modelo(batch["x"])
            probas_val.append(torch.softmax(salida["1x2"], dim=1).numpy())
            y_val.append(batch["y_1x2"].numpy())
    val_brier = brier_confianza_elegida(
        np.concatenate(y_val), np.vstack(probas_val))
    log.info(f"  Mejor val_loss: {mejor_val_loss:.4f} | val_acc_1x2: {mejor_acc_1x2*100:.2f}%")

    return {
        "modelo": modelo,
        "scaler_x": scaler_x,
        "norm_corners": (media_corners, std_corners),
        "norm_tarjetas": (media_tarjetas, std_tarjetas),
        "val_loss": mejor_val_loss,
        "val_acc": mejor_acc_1x2,
        "val_brier": val_brier,
    }


def guardar_mlp(resultado: dict, ruta: Path = MLP_PATH):
    torch.save({
        "state_dict": resultado["modelo"].state_dict(),
        "n_features": len(FEATURES_ML),
        "scaler_x_mean": resultado["scaler_x"].mean_,
        "scaler_x_scale": resultado["scaler_x"].scale_,
        "norm_corners": resultado["norm_corners"],
        "norm_tarjetas": resultado["norm_tarjetas"],
        "val_acc": resultado["val_acc"],
        "val_brier": resultado.get("val_brier"),
    }, ruta)
    log.info(f"MLP guardado: {ruta}")


def cargar_mlp(ruta: Path = MLP_PATH):
    if not ruta.exists():
        log.error(f"MLP no encontrado: {ruta}")
        return None

    checkpoint = torch.load(ruta, weights_only=False)
    modelo = RedMultiObjetivo(n_features=checkpoint["n_features"])
    modelo.load_state_dict(checkpoint["state_dict"])
    modelo.eval()

    scaler_x = StandardScaler()
    scaler_x.mean_ = checkpoint["scaler_x_mean"]
    scaler_x.scale_ = checkpoint["scaler_x_scale"]
    scaler_x.n_features_in_ = len(checkpoint["scaler_x_mean"])

    return {
        "modelo": modelo,
        "scaler_x": scaler_x,
        "norm_corners": checkpoint["norm_corners"],
        "norm_tarjetas": checkpoint["norm_tarjetas"],
        "val_acc": checkpoint.get("val_acc", 0.5),
        "val_brier": checkpoint.get("val_brier"),
    }


def predecir_mlp(cargado: dict, features_dict: dict) -> dict:
    """Predice todos los mercados para un partido dado su vector de
    features (mismo dict que devuelve construir_features_partido)."""
    modelo = cargado["modelo"]
    scaler_x = cargado["scaler_x"]

    x = np.array([[features_dict.get(f, 0) or 0 for f in FEATURES_ML]], dtype=np.float32)
    x_scaled = scaler_x.transform(x)
    x_t = torch.tensor(x_scaled, dtype=torch.float32)

    modelo.eval()
    with torch.no_grad():
        pred = modelo(x_t)

    proba_1x2 = torch.softmax(pred["1x2"], dim=1)[0].numpy()
    proba_ht = torch.softmax(pred["ht"], dim=1)[0].numpy()

    media_c, std_c = cargado["norm_corners"]
    media_t, std_t = cargado["norm_tarjetas"]

    return {
        "prob_local":     round(float(proba_1x2[0]), 4),
        "prob_empate":    round(float(proba_1x2[1]), 4),
        "prob_visitante": round(float(proba_1x2[2]), 4),
        "prob_over_2_5":  round(float(torch.sigmoid(pred["over25"])[0]), 4),
        "prob_btts":      round(float(torch.sigmoid(pred["btts"])[0]), 4),
        "corners_esperados":  round(float(pred["corners"][0]) * std_c + media_c, 2),
        "tarjetas_esperadas": round(float(pred["tarjetas"][0]) * std_t + media_t, 2),
        "prob_ht_local":   round(float(proba_ht[0]), 4),
        "prob_ht_empate":  round(float(proba_ht[1]), 4),
        "prob_ht_visitante": round(float(proba_ht[2]), 4),
    }


if __name__ == "__main__":
    from backend.features.dataset import generar_dataset

    log.info("Cargando dataset...")
    df = generar_dataset()

    if df.empty:
        log.warning("Sin datos suficientes")
    else:
        resultado = entrenar_mlp(df)
        guardar_mlp(resultado)
        log.info("MLP listo")
