"""GNN equipo-jugador — 1X2 vía message passing sobre el grafo de
backend/features/grafo.py.

Dos capas de HeteroConv (GraphSAGE por tipo de arista): cada equipo
actualiza su embedding combinando (a) su propio estado, (b) el de los
equipos que enfrentó (arista equipo-equipo), y (c) el de SUS jugadores
actuales (arista jugador-equipo) — esto último es lo que un grafo
solo-de-equipos no puede ver: dos equipos con la misma forma reciente
pero planteles distintos (uno con la figura lesionada, el otro no)
quedan diferenciados acá.

# ponytail: SAGEConv no usa edge_attr (la diferencia de gol guardada en
# el grafo) — dropea esa señal, la conectividad sí se usa. Upgrade a
# NNConv o similar si hace falta que el peso de la arista importe.
# ponytail: grafo transductivo de una sola foto (ver construir_grafo) —
# no hay una versión "solo con datos antes de este partido" por cada
# partido de entrenamiento. Snapshots por temporada si hace falta cerrar
# ese hueco.
"""
import logging
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import HeteroConv, SAGEConv
from sklearn.utils.class_weight import compute_class_weight
from backend.models.validacion import brier_confianza_elegida

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent.parent.parent
MODELS_DIR = ROOT_DIR / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
GNN_PATH = MODELS_DIR / "gnn_v1.pt"

HIDDEN = 64


def _tipos_arista(grafo):
    return list(grafo.edge_index_dict.keys())


class GNNEquipoJugador(nn.Module):
    def __init__(self, tipos_arista, hidden: int = HIDDEN):
        super().__init__()
        self.conv1 = HeteroConv({
            t: SAGEConv((-1, -1), hidden) for t in tipos_arista
        }, aggr="mean")
        self.conv2 = HeteroConv({
            t: SAGEConv((-1, -1), hidden) for t in tipos_arista
        }, aggr="mean")
        self.clasificador = nn.Sequential(
            nn.Linear(hidden * 2, 64), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(64, 3),
        )

    def embeddings(self, x_dict, edge_index_dict):
        x_dict = self.conv1(x_dict, edge_index_dict)
        x_dict = {k: F.relu(v) for k, v in x_dict.items()}
        x_dict = self.conv2(x_dict, edge_index_dict)
        return x_dict

    def forward(self, x_dict, edge_index_dict, idx_local, idx_visit):
        emb = self.embeddings(x_dict, edge_index_dict)
        emb_equipo = emb["equipo"]
        par = torch.cat([emb_equipo[idx_local], emb_equipo[idx_visit]], dim=1)
        return self.clasificador(par)


def _pares_entrenamiento(db, idx_equipo: dict, fecha_hasta=None,
                         fecha_desde=None) -> list:
    """(idx_local, idx_visit, resultado) de partidos reales — para
    entrenar el clasificador sobre los embeddings del grafo."""
    from sqlalchemy import text
    filtros, params = [], {}
    if fecha_hasta is not None:
        filtros.append("p.fecha < :fecha_hasta")
        params["fecha_hasta"] = fecha_hasta
    if fecha_desde is not None:
        filtros.append("p.fecha >= :fecha_desde")
        params["fecha_desde"] = fecha_desde
    filtro = " and " + " and ".join(filtros) if filtros else ""
    filas = db.execute(text(f"""
        select equipo_local_id, equipo_visit_id, goles_local, goles_visitante
        from partidos p
        where estado = 'FT' and goles_local is not null {filtro}
    """), params).fetchall()

    pares = []
    for f in filas:
        if f.equipo_local_id not in idx_equipo or f.equipo_visit_id not in idx_equipo:
            continue
        resultado = 0 if f.goles_local > f.goles_visitante else (
            1 if f.goles_local == f.goles_visitante else 2)
        pares.append((idx_equipo[f.equipo_local_id], idx_equipo[f.equipo_visit_id], resultado))
    return pares


def _fecha_corte_validacion(db, proporcion_validacion: float = 0.20):
    """Fecha que inicia el bloque cronológico reservado."""
    from sqlalchemy import text
    fechas = [f[0] for f in db.execute(text("""
        select fecha from partidos
        where estado = 'FT' and goles_local is not null
        order by fecha asc
    """)).fetchall()]
    if len(fechas) < 10:
        raise ValueError("Se necesitan al menos 10 partidos para validar la GNN")
    indice = min(len(fechas) - 1, int(len(fechas) * (1 - proporcion_validacion)))
    return fechas[indice]


def entrenar_gnn(db, epochs: int = 100, lr: float = 0.005, patience: int = 15) -> dict:
    from backend.features.grafo import construir_grafo

    log.info("=" * 55)
    log.info("  Entrenando GNN equipo-jugador — BetML Pro")
    log.info("=" * 55)

    fecha_corte = _fecha_corte_validacion(db)
    # El message passing tampoco puede mirar aristas/resultados futuros.
    grafo, idx_equipo, idx_jugador = construir_grafo(db, fecha_corte=fecha_corte)
    train_pares = _pares_entrenamiento(db, idx_equipo, fecha_hasta=fecha_corte)
    val_pares = _pares_entrenamiento(db, idx_equipo, fecha_desde=fecha_corte)
    if not train_pares or not val_pares:
        raise ValueError("El corte temporal dejó la GNN sin train o validación")
    log.info(f"  Corte temporal GNN: {len(train_pares)} train | "
             f"{len(val_pares)} validación desde {fecha_corte}")

    def a_tensores(pares):
        idx_l = torch.tensor([p[0] for p in pares], dtype=torch.long)
        idx_v = torch.tensor([p[1] for p in pares], dtype=torch.long)
        y = torch.tensor([p[2] for p in pares], dtype=torch.long)
        return idx_l, idx_v, y

    idx_l_train, idx_v_train, y_train = a_tensores(train_pares)
    idx_l_val, idx_v_val, y_val = a_tensores(val_pares)

    pesos_np = compute_class_weight("balanced", classes=np.array([0, 1, 2]),
                                     y=y_train.numpy())
    pesos_clase = torch.tensor(pesos_np, dtype=torch.float32)

    modelo = GNNEquipoJugador(_tipos_arista(grafo))
    optim = torch.optim.AdamW(modelo.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optim, mode="min", patience=8, factor=0.5)

    mejor_val_loss = float("inf")
    mejor_acc = 0.0
    epochs_sin_mejora = 0
    mejor_estado = None

    for epoch in range(epochs):
        modelo.train()
        optim.zero_grad()
        logits = modelo(grafo.x_dict, grafo.edge_index_dict, idx_l_train, idx_v_train)
        loss = F.cross_entropy(logits, y_train, weight=pesos_clase)
        loss.backward()
        optim.step()

        modelo.eval()
        with torch.no_grad():
            logits_val = modelo(grafo.x_dict, grafo.edge_index_dict, idx_l_val, idx_v_val)
            loss_val = F.cross_entropy(logits_val, y_val, weight=pesos_clase).item()
            acc_val = (logits_val.argmax(dim=1) == y_val).float().mean().item()

        scheduler.step(loss_val)

        if epoch % 10 == 0 or epoch == epochs - 1:
            log.info(f"  epoch {epoch:>3} | train_loss={loss.item():.4f} "
                      f"val_loss={loss_val:.4f} val_acc={acc_val*100:.2f}%")

        if loss_val < mejor_val_loss:
            mejor_val_loss = loss_val
            mejor_acc = acc_val
            mejor_estado = {k: v.clone() for k, v in modelo.state_dict().items()}
            epochs_sin_mejora = 0
        else:
            epochs_sin_mejora += 1
            if epochs_sin_mejora >= patience:
                log.info(f"  Early stopping en epoch {epoch}")
                break

    modelo.load_state_dict(mejor_estado)
    modelo.eval()
    with torch.no_grad():
        logits_val = modelo(grafo.x_dict, grafo.edge_index_dict, idx_l_val, idx_v_val)
        val_brier = brier_confianza_elegida(
            y_val.numpy(), torch.softmax(logits_val, dim=1).numpy())
    log.info(f"  Mejor val_loss: {mejor_val_loss:.4f} | val_acc: {mejor_acc*100:.2f}%")

    # La métrica se obtuvo con un grafo congelado antes del corte. Para
    # servir predicciones sí incorporamos la foto completa actual; los
    # pesos no vuelven a evaluarse sobre ella, por lo que val_acc conserva
    # su significado y equipos recientes no desaparecen de producción.
    grafo_prod, idx_equipo_prod, idx_jugador_prod = construir_grafo(db)

    return {
        "modelo": modelo, "grafo": grafo_prod, "idx_equipo": idx_equipo_prod,
        "idx_jugador": idx_jugador_prod, "val_acc": mejor_acc,
        "val_brier": val_brier,
    }


def guardar_gnn(resultado: dict, ruta: Path = GNN_PATH):
    torch.save({
        "state_dict": resultado["modelo"].state_dict(),
        "tipos_arista": _tipos_arista(resultado["grafo"]),
        "grafo": resultado["grafo"],
        "idx_equipo": resultado["idx_equipo"],
        "idx_jugador": resultado["idx_jugador"],
        "val_acc": resultado["val_acc"],
        "val_brier": resultado.get("val_brier"),
    }, ruta)
    log.info(f"GNN guardada: {ruta}")


def cargar_gnn(ruta: Path = GNN_PATH):
    if not ruta.exists():
        log.error(f"GNN no encontrada: {ruta}")
        return None
    checkpoint = torch.load(ruta, weights_only=False)
    modelo = GNNEquipoJugador(checkpoint["tipos_arista"])
    modelo.load_state_dict(checkpoint["state_dict"])
    modelo.eval()
    return {
        "modelo": modelo, "grafo": checkpoint["grafo"],
        "idx_equipo": checkpoint["idx_equipo"], "idx_jugador": checkpoint["idx_jugador"],
        "val_acc": checkpoint["val_acc"],
        "val_brier": checkpoint.get("val_brier"),
    }


def predecir_gnn(cargado: dict, equipo_local_id: int, equipo_visit_id: int) -> dict | None:
    idx_equipo = cargado["idx_equipo"]
    if equipo_local_id not in idx_equipo or equipo_visit_id not in idx_equipo:
        return None

    modelo, grafo = cargado["modelo"], cargado["grafo"]
    idx_l = torch.tensor([idx_equipo[equipo_local_id]], dtype=torch.long)
    idx_v = torch.tensor([idx_equipo[equipo_visit_id]], dtype=torch.long)

    modelo.eval()
    with torch.no_grad():
        logits = modelo(grafo.x_dict, grafo.edge_index_dict, idx_l, idx_v)
    proba = torch.softmax(logits, dim=1)[0].numpy()

    return {
        "prob_local": round(float(proba[0]), 4),
        "prob_empate": round(float(proba[1]), 4),
        "prob_visitante": round(float(proba[2]), 4),
    }


if __name__ == "__main__":
    from backend.db.database import SessionLocal
    db = SessionLocal()
    resultado = entrenar_gnn(db)
    guardar_gnn(resultado)
    db.close()
    log.info("GNN lista")
