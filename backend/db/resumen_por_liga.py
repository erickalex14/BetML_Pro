from backend.db.database import SessionLocal
from backend.db.modelos import Partido, EstadisticaPartido
from backend.pipeline.config import LIGAS, TEMPORADA_ACTUAL

db = SessionLocal()

print("=" * 65)
print("  Partidos por liga — Temporada actual")
print("=" * 65)
print(f"  {'Liga':<25} {'Temp':>6} {'FT':>6} {'Stats':>6} {'Faltan':>8}")
print("-" * 65)

total_ft      = 0
total_stats   = 0
total_faltan  = 0

for nombre_liga, liga_id in LIGAS.items():
    temporada = TEMPORADA_ACTUAL[nombre_liga]

    ft = (
        db.query(Partido)
        .filter(
            Partido.liga_id   == liga_id,
            Partido.temporada == temporada,
            Partido.estado    == "FT"
        )
        .count()
    )

    con_stats = (
        db.query(Partido)
        .join(EstadisticaPartido)
        .filter(
            Partido.liga_id   == liga_id,
            Partido.temporada == temporada,
            Partido.estado    == "FT"
        )
        .count()
    )

    faltan = ft - con_stats

    total_ft    += ft
    total_stats += con_stats
    total_faltan+= faltan

    # Marca en rojo (con asterisco) las ligas sin datos
    alerta = " ←" if ft == 0 else ""

    print(
        f"  {nombre_liga:<25} {temporada:>6} "
        f"{ft:>6} {con_stats:>6} {faltan:>8}{alerta}"
    )

print("-" * 65)
print(
    f"  {'TOTAL':<25} {'':>6} "
    f"{total_ft:>6} {total_stats:>6} {total_faltan:>8}"
)
print("=" * 65)

db.close()