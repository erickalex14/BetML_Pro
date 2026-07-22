import logging
import pandas as pd
from backend.db.database import SessionLocal
from backend.db.modelos import Partido
from backend.features.calculador import construir_features_partido

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)


def generar_dataset(temporadas: list = [2023, 2024]) -> pd.DataFrame:
    """
    Genera el dataset completo de features para todas las
    temporadas indicadas. Solo incluye partidos terminados (FT)
    con suficiente historial para calcular features.

    Retorna un DataFrame de pandas listo para entrenar XGBoost.
    """
    log.info("=" * 50)
    log.info("Generando dataset de features")
    log.info("=" * 50)

    db = SessionLocal()
    filas = []
    procesados = 0
    descartados = 0

    try:
        # Trae todos los partidos FT de las temporadas indicadas
        # ordenados por fecha — importante para que el H2H
        # y la forma se calculen en orden cronológico correcto
        partidos = (
            db.query(Partido)
            .filter(
                Partido.temporada.in_(temporadas),
                Partido.estado == "FT",
                Partido.goles_local != None
            )
            .order_by(Partido.fecha.asc())
            .all()
        )

        total = len(partidos)
        log.info(f"Partidos FT encontrados: {total}")

        for i, partido in enumerate(partidos):
            features = construir_features_partido(db, partido)

            if features is None:
                descartados += 1
                continue

            filas.append(features)
            procesados += 1

            # Log de progreso cada 500 partidos
            if (i + 1) % 500 == 0:
                log.info(f"Progreso: {i+1}/{total} partidos procesados")

    finally:
        db.close()

    df = pd.DataFrame(filas)

    log.info(f"\nDataset generado:")
    log.info(f"  Partidos procesados : {procesados}")
    log.info(f"  Partidos descartados: {descartados} (sin historial)")
    log.info(f"  Shape del dataset   : {df.shape}")
    if not df.empty:
        log.info(f"  Distribución target :")
        dist = df["resultado"].value_counts().sort_index()
        log.info(f"    0 (local gana) : {dist.get(0, 0)}")
        log.info(f"    1 (empate)     : {dist.get(1, 0)}")
        log.info(f"    2 (visit gana) : {dist.get(2, 0)}")

    return df


if __name__ == "__main__":
    df = generar_dataset(temporadas=[2023, 2024])
    if not df.empty:
        print("\nPrimeras 3 filas del dataset:")
        print(df.head(3).to_string())
        print(f"\nColumnas: {list(df.columns)}")