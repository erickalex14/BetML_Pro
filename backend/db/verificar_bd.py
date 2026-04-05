from backend.db.database import SessionLocal
from backend.db.modelos import Partido, Equipo

db = SessionLocal()

# Cuenta registros en cada tabla
partidos = db.query(Partido).count()
equipos  = db.query(Equipo).count()

print(f"Partidos guardados: {partidos}")
print(f"Equipos guardados:  {equipos}")
print()

# Muestra los primeros 5 partidos
print("Primeros 5 partidos:")
print("-" * 50)

for p in db.query(Partido).limit(5).all():
    local = db.get(Equipo, p.equipo_local_id).nombre
    visitante = db.get(Equipo, p.equipo_visit_id).nombre
    hora      = str(p.fecha)[11:16]
    print(f"  {hora} — {local} vs {visitante} | Estado: {p.estado}")

db.close()

