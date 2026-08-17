"""Red LSTM — captura la dimensión temporal que XGBoost y el MLP no ven.
calcular_forma() promedia los últimos 5 partidos en un número; para el
modelo, perder 3-0, 2-0 y 1-0 seguidos es indistinguible de un empate
1-1 y dos victorias 1-0 (mismo promedio de goles). El LSTM procesa la
secuencia entera y sí distingue una racha de una mezcla.

Arquitectura: por cada equipo, sus últimos 10 partidos (goles, resultado,
xG, posesión, local/visitante) pasan por un LSTM bidireccional de 2
capas (hidden_size=128) compartido entre ambos equipos del partido.
Atención temporal pondera qué pasos de la secuencia importan más para
este partido en particular, en vez de solo tomar el último estado
oculto. Los dos vectores de contexto (local + visitante) se concatenan
y pasan por un clasificador chico para 1X2.

Por qué comparten pesos el codificador de local y visitante: la dinámica
de "qué significa una racha de resultados" es la misma independientemente
de si el equipo juega hoy de local o de visitante — es una propiedad del
equipo, no del partido. Compartir pesos también reduce a la mitad los
parámetros a entrenar con el dataset que hay disponible.
"""
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.nn.utils.rnn import pad_sequence
from sklearn.utils.class_weight import compute_class_weight

from backend.db.database import SessionLocal
from backend.db.modelos import Partido
from backend.features.calculador import obtener_secuencia_equipo, N_DIMS_SECUENCIA
from backend.models.validacion import division_temporal, brier_confianza_elegida

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent.parent.parent
MODELS_DIR = ROOT_DIR / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
LSTM_PATH = MODELS_DIR / "lstm_v1.pt"

LONGITUD_SECUENCIA = 10
HIDDEN_SIZE = 128


class CodificadorTemporal(nn.Module):
    """LSTM bidireccional 2 capas + atención -> un vector de contexto
    de tamaño hidden_size*2 por secuencia de partidos."""

    def __init__(self, n_dims: int, hidden_size: int = HIDDEN_SIZE):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=n_dims, hidden_size=hidden_size,
            num_layers=2, batch_first=True, bidirectional=True, dropout=0.2,
        )
        # Atención aditiva simple: un score por paso temporal, softmax,
        # suma ponderada de las salidas del LSTM.
        self.atencion = nn.Linear(hidden_size * 2, 1)

    def forward(self, x, longitudes):
        # x: (batch, seq_len, n_dims) con padding a la izquierda en los
        # partidos con menos de LONGITUD_SECUENCIA de historial
        salidas, _ = self.lstm(x)  # (batch, seq_len, hidden*2)

        scores = self.atencion(salidas).squeeze(-1)  # (batch, seq_len)

        # Máscara: los pasos de padding (más allá de la longitud real de
        # cada secuencia) no deben competir en el softmax de atención
        mascara = torch.arange(x.size(1), device=x.device)[None, :] >= (
            x.size(1) - longitudes[:, None])
        scores = scores.masked_fill(~mascara, float("-inf"))
        pesos = torch.softmax(scores, dim=1).unsqueeze(-1)  # (batch, seq_len, 1)

        contexto = (salidas * pesos).sum(dim=1)  # (batch, hidden*2)
        return contexto


class RedLSTM(nn.Module):
    def __init__(self, n_dims: int = N_DIMS_SECUENCIA, hidden_size: int = HIDDEN_SIZE):
        super().__init__()
        self.codificador = CodificadorTemporal(n_dims, hidden_size)  # pesos compartidos
        self.clasificador = nn.Sequential(
            nn.Linear(hidden_size * 2 * 2, 64), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(64, 3),
        )

    def forward(self, seq_local, len_local, seq_visit, len_visit):
        ctx_local = self.codificador(seq_local, len_local)
        ctx_visit = self.codificador(seq_visit, len_visit)
        contexto_completo = torch.cat([ctx_local, ctx_visit], dim=1)
        return self.clasificador(contexto_completo), contexto_completo


def _pad_izquierda(secuencia: list, longitud: int = LONGITUD_SECUENCIA) -> np.ndarray:
    """Rellena con ceros al INICIO — los pasos reales quedan pegados al
    final, que es donde el LSTM procesal la información más reciente."""
    arr = np.zeros((longitud, N_DIMS_SECUENCIA), dtype=np.float32)
    n = min(len(secuencia), longitud)
    if n > 0:
        arr[longitud - n:] = np.array(secuencia[-n:], dtype=np.float32)
    return arr


class _DatasetSecuencias(Dataset):
    """Construye las secuencias local/visitante para cada partido del
    dataframe. df debe traer partido_id (generar_dataset ya lo incluye)."""

    def __init__(self, df: pd.DataFrame):
        db = SessionLocal()
        self.seq_local, self.len_local = [], []
        self.seq_visit, self.len_visit = [], []
        self.y = []

        partidos_por_id = {
            p.id: p for p in db.query(Partido)
            .filter(Partido.id.in_(df["partido_id"].tolist())).all()
        }

        for _, fila in df.iterrows():
            partido = partidos_por_id.get(fila["partido_id"])
            if partido is None:
                continue

            sl = obtener_secuencia_equipo(db, partido.equipo_local_id, partido.fecha, LONGITUD_SECUENCIA)
            sv = obtener_secuencia_equipo(db, partido.equipo_visit_id, partido.fecha, LONGITUD_SECUENCIA)

            self.seq_local.append(_pad_izquierda(sl))
            self.len_local.append(len(sl))
            self.seq_visit.append(_pad_izquierda(sv))
            self.len_visit.append(len(sv))
            self.y.append(int(fila["resultado"]))

        db.close()

        self.seq_local = torch.tensor(np.array(self.seq_local), dtype=torch.float32)
        self.len_local = torch.tensor(self.len_local, dtype=torch.long)
        self.seq_visit = torch.tensor(np.array(self.seq_visit), dtype=torch.float32)
        self.len_visit = torch.tensor(self.len_visit, dtype=torch.long)
        self.y = torch.tensor(self.y, dtype=torch.long)

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        return {
            "seq_local": self.seq_local[idx], "len_local": self.len_local[idx],
            "seq_visit": self.seq_visit[idx], "len_visit": self.len_visit[idx],
            "y": self.y[idx],
        }


def entrenar_lstm(df: pd.DataFrame, epochs: int = 40, batch_size: int = 64,
                   lr: float = 0.001, patience: int = 6) -> dict:
    log.info("=" * 55)
    log.info("  Entrenando LSTM — BetML Pro")
    log.info("=" * 55)
    log.info("  Construyendo secuencias temporales (consulta BD por partido)...")

    df_train, df_val = division_temporal(df)
    log.info(f"  Corte temporal: train hasta {df_train['fecha'].max()} | "
             f"validación desde {df_val['fecha'].min()}")

    ds_train = _DatasetSecuencias(df_train)
    ds_val = _DatasetSecuencias(df_val)
    log.info(f"  Secuencias listas: {len(ds_train)} train, {len(ds_val)} val")

    dl_train = DataLoader(ds_train, batch_size=batch_size, shuffle=True)
    dl_val = DataLoader(ds_val, batch_size=batch_size, shuffle=False)

    modelo = RedLSTM()
    optim = torch.optim.AdamW(modelo.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optim, mode="min", patience=4, factor=0.5)

    # Empate ~25% de los partidos — sin pesos balanceados el modelo
    # aprende a no predecirlo nunca (mismo problema que en XGBoost/MLP,
    # ver entrenador.py).
    pesos_np = compute_class_weight("balanced", classes=np.array([0, 1, 2]),
                                     y=df_train["resultado"].to_numpy())
    ce = nn.CrossEntropyLoss(weight=torch.tensor(pesos_np, dtype=torch.float32))

    mejor_val_loss = float("inf")
    epochs_sin_mejora = 0
    mejor_estado = None

    for epoch in range(epochs):
        modelo.train()
        loss_train = 0.0
        for batch in dl_train:
            optim.zero_grad()
            logits, _ = modelo(batch["seq_local"], batch["len_local"],
                                batch["seq_visit"], batch["len_visit"])
            loss = ce(logits, batch["y"])
            loss.backward()
            optim.step()
            loss_train += loss.item() * len(batch["y"])
        loss_train /= len(ds_train)

        modelo.eval()
        loss_val = 0.0
        aciertos = 0
        with torch.no_grad():
            for batch in dl_val:
                logits, _ = modelo(batch["seq_local"], batch["len_local"],
                                    batch["seq_visit"], batch["len_visit"])
                loss = ce(logits, batch["y"])
                loss_val += loss.item() * len(batch["y"])
                aciertos += (logits.argmax(dim=1) == batch["y"]).sum().item()
        loss_val /= len(ds_val)
        acc = aciertos / len(ds_val)

        scheduler.step(loss_val)

        if epoch % 5 == 0 or epoch == epochs - 1:
            log.info(f"  epoch {epoch:>3} | train_loss={loss_train:.4f} "
                      f"val_loss={loss_val:.4f} val_acc={acc*100:.2f}%")

        if loss_val < mejor_val_loss:
            mejor_val_loss = loss_val
            mejor_acc = acc
            mejor_estado = {k: v.clone() for k, v in modelo.state_dict().items()}
            epochs_sin_mejora = 0
        else:
            epochs_sin_mejora += 1
            if epochs_sin_mejora >= patience:
                log.info(f"  Early stopping en epoch {epoch}")
                break

    modelo.load_state_dict(mejor_estado)
    probas_val, y_val = [], []
    modelo.eval()
    with torch.no_grad():
        for batch in dl_val:
            logits, _ = modelo(batch["seq_local"], batch["len_local"],
                               batch["seq_visit"], batch["len_visit"])
            probas_val.append(torch.softmax(logits, dim=1).numpy())
            y_val.append(batch["y"].numpy())
    val_brier = brier_confianza_elegida(
        np.concatenate(y_val), np.vstack(probas_val))
    log.info(f"  Mejor val_loss: {mejor_val_loss:.4f} | val_acc: {mejor_acc*100:.2f}%")

    return {"modelo": modelo, "val_loss": mejor_val_loss,
            "val_acc": mejor_acc, "val_brier": val_brier}


def guardar_lstm(resultado: dict, ruta: Path = LSTM_PATH):
    torch.save({
        "state_dict": resultado["modelo"].state_dict(),
        "val_acc": resultado["val_acc"],
        "val_brier": resultado.get("val_brier"),
    }, ruta)
    log.info(f"LSTM guardado: {ruta}")


def cargar_lstm(ruta: Path = LSTM_PATH):
    if not ruta.exists():
        log.error(f"LSTM no encontrado: {ruta}")
        return None
    checkpoint = torch.load(ruta, weights_only=False)
    modelo = RedLSTM()
    modelo.load_state_dict(checkpoint["state_dict"])
    modelo.eval()
    return {"modelo": modelo, "val_acc": checkpoint["val_acc"],
            "val_brier": checkpoint.get("val_brier")}


def predecir_lstm(cargado: dict, db, equipo_local_id: int, equipo_visit_id: int,
                   fecha) -> dict:
    modelo = cargado["modelo"]
    sl = obtener_secuencia_equipo(db, equipo_local_id, fecha, LONGITUD_SECUENCIA)
    sv = obtener_secuencia_equipo(db, equipo_visit_id, fecha, LONGITUD_SECUENCIA)

    seq_local = torch.tensor(_pad_izquierda(sl), dtype=torch.float32).unsqueeze(0)
    len_local = torch.tensor([len(sl)], dtype=torch.long)
    seq_visit = torch.tensor(_pad_izquierda(sv), dtype=torch.float32).unsqueeze(0)
    len_visit = torch.tensor([len(sv)], dtype=torch.long)

    modelo.eval()
    with torch.no_grad():
        logits, contexto = modelo(seq_local, len_local, seq_visit, len_visit)
    proba = torch.softmax(logits, dim=1)[0].numpy()

    return {
        "prob_local":     round(float(proba[0]), 4),
        "prob_empate":    round(float(proba[1]), 4),
        "prob_visitante": round(float(proba[2]), 4),
        "contexto":       contexto[0].numpy(),  # para el ensemble, si hace falta
    }


if __name__ == "__main__":
    from backend.features.dataset import generar_dataset

    log.info("Cargando dataset...")
    df = generar_dataset()

    if df.empty:
        log.warning("Sin datos suficientes")
    else:
        resultado = entrenar_lstm(df)
        guardar_lstm(resultado)
        log.info("LSTM listo")
