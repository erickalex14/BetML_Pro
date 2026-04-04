import logging
from datetime import datetime
from sqlalchemy.orm import Session
from backend.db.modelos import Liga, Equipo, Partido

log = logging.getLogger(__name__)

"""
Recibe un fixture de API-Football (diccionario)
y lo guarda en la tabla partidos.

Si el partido ya existe (mismo ID), lo actualiza.
Si no existe, lo crea. — Patrón UPSERT.
si tiene ID existente actualiza, si no crea nuevo.
"""
def guardar_partido(db: Session, fixture: dict, liga_id: int, temporada: int):
    fixture_id  = fixture["fixture"]["id"]
    fecha_str   = fixture["fixture"]["date"]
    estado      = fixture["fixture"]["status"]["short"]
    jornada     = fixture["league"]["round"]
    local_id    = fixture["teams"]["home"]["id"]
    local_nombre= fixture["teams"]["home"]["name"]
    visit_id    = fixture["teams"]["away"]["id"]
    visit_nombre= fixture["teams"]["away"]["name"]
    goles_l     = fixture["goals"]["home"]
    goles_v     = fixture["goals"]["away"]
    # Goles al descanso — pueden ser None si no terminó
    ht          = fixture["score"]["halftime"]
    goles_l_ht  = ht["home"]
    goles_v_ht  = ht["away"]
    fecha = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
    # Guardar o actualizar los equipos
    _upsert_equipo(db, local_id, local_nombre)
    _upsert_equipo(db, visit_id, visit_nombre)

    partido = db.get(Partido, fixture_id)

    if partido is None:
        #Si no existe crear nuevo
        partido = Partido(
            id=fixture_id,
            liga_id=liga_id,
            temporada=temporada,
            equipo_local_id=local_id,
            equipo_visit_id=visit_id,
            fecha=fecha,
            jornada=jornada,
        )
        db.add(partido)
        log.info(f"Nuevo partido: {local_nombre} vs {visit_nombre}")
    else:
        log.info(f"Actualizando: {local_nombre} vs {visit_nombre}")

    #Actualiza campos que pueden cambiar
    partido.estado          = estado
    partido.goles_local     = goles_l
    partido.goles_visitante = goles_v
    partido.goles_local_ht  = goles_l_ht
    partido.goles_visit_ht  = goles_v_ht
    partido.actualizado_en  = datetime.utcnow()
    # db.commit() escribe los cambios en disco
    # Sin esto los cambios están solo en memoria

    db.commit()
    return partido

#Metodo auxiliar

def _upsert_equipo(db: Session, equipo_id: int, nombre: str):
    """
    Crea el equipo si no existe, no hace nada si ya está.
    El _ al inicio indica que es función privada de este módulo.
    """
    equipo = db.get(Equipo, equipo_id)
    if equipo is None:
        equipo = Equipo(id=equipo_id, nombre=nombre)
        db.add(equipo)
        db.commit()





