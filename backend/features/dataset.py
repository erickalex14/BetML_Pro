import logging
from pathlib import Path
import pandas as pd
from backend.db.database import SessionLocal, crear_tablas
from backend.db.modelos import Partido
from backend.features.calculador import construir_features_partido

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent.parent.parent
CACHE_PATH = ROOT_DIR / "data" / "dataset_features.pkl"

# Lista completa de features que usa el modelo
# El orden importa — XGBoost entrena con este orden
FEATURES_ML = [
    # Forma básica
    "forma_local_puntos", "forma_local_gf", "forma_local_gc",
    "forma_visit_puntos", "forma_visit_gf", "forma_visit_gc",

    # Win rates
    "win_rate_local", "win_rate_visit",

    # H2H
    "h2h_wins_local", "h2h_empates", "h2h_wins_visit",
    "h2h_goles_local", "h2h_goles_visit",

    # Sofascore avanzadas — local
    "xg_favor_local", "xg_contra_local",
    "tiros_favor_local", "tiros_arco_fav_local",
    "corners_fav_local", "presiones_local", "posesion_local",

    # Sofascore avanzadas — visitante
    "xg_favor_visit", "xg_contra_visit",
    "tiros_favor_visit", "tiros_arco_fav_visit",
    "corners_fav_visit", "presiones_visit", "posesion_visit",

    # Ratings jugadores
    "rating_local", "rating_visit",
]

TARGET = "resultado"


def generar_dataset(temporadas: list = [2023, 2024, 2025, 2026],
                     usar_cache: bool = True) -> pd.DataFrame:
    # La generación recorre cada partido con ~9 queries a BD (forma, H2H,
    # stats Sofascore, ratings) — con miles de partidos tarda minutos.
    # Cachea a disco para no repetir ese costo en cada reentrenamiento;
    # usar_cache=False fuerza recalcular (ej: tras cambiar el feature
    # engineering, como pasó con el fix del leakage de rating_local).
    if usar_cache and CACHE_PATH.exists():
        df = pd.read_pickle(CACHE_PATH)
        if sorted(df["temporada"].unique().tolist()) == sorted(set(temporadas)):
            log.info(f"Dataset cacheado: {CACHE_PATH} ({df.shape[0]} partidos)")
            return df
        log.info("Cache no coincide con las temporadas pedidas — regenerando")

    log.info("=" * 55)
    log.info("  Generando dataset de features — BetML Pro")
    log.info("=" * 55)

    crear_tablas()
    db = SessionLocal()
    filas       = []
    procesados  = 0
    descartados = 0

    try:
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

            if (i + 1) % 1000 == 0:
                log.info(f"Progreso: {i+1}/{total}")

    finally:
        db.close()

    df = pd.DataFrame(filas)

    log.info(f"\n  Partidos procesados : {procesados}")
    log.info(f"  Partidos descartados: {descartados}")

    if df.empty:
        log.warning("Dataset vacío — no hay suficientes datos")
        return df

    log.info(f"  Shape del dataset   : {df.shape}")
    log.info(f"  Features con Sofascore:")
    log.info(f"    Partidos con xG   : {(df['xg_favor_local'] > 0).sum()}")
    log.info(f"    Partidos con rating: {(df['rating_local'] > 0).sum()}")
    log.info(f"\n  Distribución target:")
    dist = df["resultado"].value_counts().sort_index()
    log.info(f"    Local gana  (0): {dist.get(0, 0)}")
    log.info(f"    Empate      (1): {dist.get(1, 0)}")
    log.info(f"    Visit gana  (2): {dist.get(2, 0)}")

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_pickle(CACHE_PATH)
    log.info(f"Dataset cacheado en {CACHE_PATH}")

    return df


if __name__ == "__main__":
    df = generar_dataset()
    if not df.empty:
        print(f"\nPrimeras 2 filas:")
        print(df[FEATURES_ML].head(2).to_string())