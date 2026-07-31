from backend.db.database import SessionLocal
from backend.db.modelos import Partido, EstadisticaSofascore
from backend.pipeline.config import LIGAS

db = SessionLocal()

print("=" * 65)
print("  Partidos por liga — TODAS las temporadas")
print("=" * 65)
print(f"  {'Liga':<25} {'2023':>6} {'2024':>6} {'Total':>7}")
print("-" * 65)

total_general = 0

for nombre_liga, liga_id in LIGAS.items():
    t2023 = (
        db.query(Partido)
        .filter(Partido.liga_id == liga_id, Partido.temporada == 2023)
        .count()
    )
    t2024 = (
        db.query(Partido)
        .filter(Partido.liga_id == liga_id, Partido.temporada == 2024)
        .count()
    )
    total = t2023 + t2024
    total_general += total

    alerta = " ←" if total == 0 else ""
    print(f"  {nombre_liga:<25} {t2023:>6} {t2024:>6} {total:>7}{alerta}")

print("-" * 65)
print(f"  {'TOTAL':<25} {'':>6} {'':>6} {total_general:>7}")
print("=" * 65)

# Total general de la BD
total_bd     = db.query(Partido).count()
total_equipos= db.query(__import__('backend.db.modelos', fromlist=['Equipo']).Equipo).count()
print(f"\n  Total partidos en BD : {total_bd}")
print(f"  Total equipos en BD  : {total_equipos}")

db.close()