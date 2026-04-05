from backend.db.database import SessionLocal
from backend.db.modelos import Partido, Equipo, EstadisticaPartido

db = SessionLocal()

# Temporadas actuales por tipo de liga
TEMPORADAS_ACTUALES = [2025, 2026]

partidos_total = db.query(Partido).count()
partidos_ft    = db.query(Partido).filter(Partido.estado == "FT").count()
equipos        = db.query(Equipo).count()
stats          = db.query(EstadisticaPartido).count()

# Partidos FT de temporada actual sin stats
pendientes_stats = (
    db.query(Partido)
    .outerjoin(EstadisticaPartido)
    .filter(
        Partido.estado.in_(["FT"]),
        Partido.temporada.in_(TEMPORADAS_ACTUALES),
        EstadisticaPartido.id == None
    )
    .count()
)

# Partidos FT de temporada actual CON stats
con_stats = (
    db.query(Partido)
    .join(EstadisticaPartido)
    .filter(
        Partido.temporada.in_(TEMPORADAS_ACTUALES),
        Partido.estado == "FT",
    )
    .count()
)

# Total FT de temporada actual
total_temporada_actual = (
    db.query(Partido)
    .filter(
        Partido.temporada.in_(TEMPORADAS_ACTUALES),
        Partido.estado == "FT"
    )
    .count()
)

print("=" * 50)
print("  Estado actual de la BD — BetML Pro")
print("=" * 50)
print(f"  Equipos registrados        : {equipos}")
print(f"  Partidos totales (todas)   : {partidos_total}")
print(f"  Partidos FT (todas)        : {partidos_ft}")
print()
print(f"  ── Temporada actual (2025/2026) ──")
print(f"  Partidos FT temporada actual : {total_temporada_actual}")
print(f"  Con stats                    : {con_stats}")
print(f"  Sin stats (pendientes)       : {pendientes_stats}")
print(f"  Stats guardadas total        : {stats}")
print("=" * 50)
print(f"\n  Requests para completar temporada actual:")
print(f"  {pendientes_stats} requests necesarios")
print(f"  A 60 req/día  → {pendientes_stats // 60 + 1} días aprox")
print(f"  A 80 req/día  → {pendientes_stats // 80 + 1} días aprox")
print(f"  A 98 req/día  → {pendientes_stats // 98 + 1} días aprox")
print("=" * 50)

db.close()