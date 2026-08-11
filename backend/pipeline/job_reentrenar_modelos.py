"""Reentrena XGBoost, MLP, LSTM, GNN y reajusta Dixon-Coles con los
datos más recientes — así es como "los modelos aprenden de resultados
pasados" en la práctica: no hay un mecanismo online que ajuste pesos
partido a partido, es reentreno periódico completo con el dataset
creciendo (más partidos cerrados, más xG/stats de Sofascore, más
cuotas) — el mismo mecanismo con el que se entrenó todo en desarrollo,
ahora agendado en vez de manual.

Fuerza usar_cache=False en generar_dataset(): el cache de dataset.py
compara la LISTA de temporadas pedida, no la cantidad de filas — un
reentreno "automático" con cache prendido seguiría usando el mismo
dataset viejo para siempre, nunca vería los partidos que se cerraron
esta semana.
"""
import logging
from backend.features.dataset import generar_dataset
from backend.models.entrenador import entrenar_modelo, guardar_modelo
from backend.models.mlp import entrenar_mlp, guardar_mlp
from backend.models.lstm import entrenar_lstm, guardar_lstm
from backend.models.gnn import entrenar_gnn, guardar_gnn
from backend.models.montecarlo import ajustar_rho_dixon_coles
from backend.db.database import SessionLocal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)


def correr_reentrenamiento_completo():
    log.info("=" * 55)
    log.info("  Reentrenamiento periódico — BetML Pro")
    log.info("=" * 55)

    df = generar_dataset(usar_cache=False)
    if df.empty:
        log.warning("Dataset vacío — aborto reentrenamiento")
        return
    log.info(f"Dataset fresco: {df.shape[0]} partidos")

    resultado_xgb = entrenar_modelo(df)
    if resultado_xgb[0]:
        modelo, _, _, _, accuracy = resultado_xgb
        guardar_modelo(modelo, accuracy=accuracy)
        log.info(f"XGBoost reentrenado — accuracy {accuracy:.4f}")

    resultado_mlp = entrenar_mlp(df)
    guardar_mlp(resultado_mlp)
    log.info(f"MLP reentrenado — val_acc {resultado_mlp['val_acc']:.4f}")

    resultado_lstm = entrenar_lstm(df)
    guardar_lstm(resultado_lstm)
    log.info(f"LSTM reentrenado — val_acc {resultado_lstm['val_acc']:.4f}")

    db = SessionLocal()
    try:
        resultado_gnn = entrenar_gnn(db)
        guardar_gnn(resultado_gnn)
        log.info(f"GNN reentrenada — val_acc {resultado_gnn['val_acc']:.4f}")

        ajustar_rho_dixon_coles(db)
        log.info("rho Dixon-Coles reajustado con datos frescos")
    finally:
        db.close()

    log.info("=" * 55)
    log.info("  Reentrenamiento completo")
    log.info("=" * 55)


if __name__ == "__main__":
    correr_reentrenamiento_completo()
