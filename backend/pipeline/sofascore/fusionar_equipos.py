"""Fusiona filas duplicadas del mismo equipo.

Un club terminaba cargado dos veces cuando entraba por dos caminos
distintos: una fila creada por API-Football (al aparecer en una copa) y
otra creada al importar su liga desde Sofascore, porque la búsqueda de
candidatos miraba solo dentro de la liga que se estaba importando (ya
corregido en equipos.py).

El daño no es cosmético: el partido de hoy apunta a una fila y todo el
historial cuelga de la otra, así que el modelo ve un equipo sin pasado
y se niega a predecir. Caso real (2026-08-13): Mirassol vs LDU de Quito
por Libertadores no tenía predicción; Mirassol figuraba con 0 partidos
en la fila que usaba el partido y con 58 en la duplicada.

Criterio: sobrevive la fila con sofascore_id (es la que trae historial
importado); si ninguna lo tiene, la que más partidos tenga. Las
referencias de partidos y stats se repuntan a esa, y la otra se borra.
"""
import logging
from collections import defaultdict

from sqlalchemy import func

from backend.db.database import SessionLocal
from backend.db.modelos import Partido, Equipo, EstadisticaJugador

log = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def _normalizar(nombre: str) -> str:
    import unicodedata
    sin_acentos = unicodedata.normalize("NFKD", nombre or "")
    sin_acentos = "".join(c for c in sin_acentos if not unicodedata.combining(c))
    return " ".join("".join(
        c if c.isalnum() else " " for c in sin_acentos.lower()).split())


def _partidos_de(db, equipo_id: int) -> int:
    return (db.query(Partido)
            .filter((Partido.equipo_local_id == equipo_id)
                    | (Partido.equipo_visit_id == equipo_id))
            .count())


def encontrar_duplicados(db) -> list:
    """[(sobreviviente, [a_fusionar...])] por nombre normalizado."""
    por_nombre = defaultdict(list)
    for equipo in db.query(Equipo).all():
        clave = _normalizar(equipo.nombre)
        if clave:
            por_nombre[clave].append(equipo)

    grupos = []
    for clave, equipos in por_nombre.items():
        if len(equipos) < 2:
            continue
        # gana el que tiene sofascore_id; a igualdad, el de más partidos
        equipos.sort(key=lambda e: (e.sofascore_id is not None,
                                    _partidos_de(db, e.id)), reverse=True)
        grupos.append((equipos[0], equipos[1:]))
    return grupos


def fusionar(db, sobreviviente: Equipo, duplicados: list) -> int:
    movidos = 0
    for dup in duplicados:
        movidos += (db.query(Partido)
                    .filter(Partido.equipo_local_id == dup.id)
                    .update({Partido.equipo_local_id: sobreviviente.id},
                            synchronize_session=False))
        movidos += (db.query(Partido)
                    .filter(Partido.equipo_visit_id == dup.id)
                    .update({Partido.equipo_visit_id: sobreviviente.id},
                            synchronize_session=False))
        db.query(EstadisticaJugador).filter(
            EstadisticaJugador.equipo_id == dup.id
        ).update({EstadisticaJugador.equipo_id: sobreviviente.id},
                 synchronize_session=False)

        # el sobreviviente se queda con el sofascore_id si le faltaba
        if not sobreviviente.sofascore_id and dup.sofascore_id:
            sobreviviente.sofascore_id = dup.sofascore_id
        if not sobreviviente.logo_url and dup.logo_url:
            sobreviviente.logo_url = dup.logo_url

        db.delete(dup)
    db.commit()
    return movidos


def correr_fusion(solo_listar: bool = False) -> int:
    db = SessionLocal()
    try:
        grupos = encontrar_duplicados(db)
        log.info(f"Equipos duplicados encontrados: {len(grupos)}")
        total = 0
        for sobreviviente, duplicados in grupos:
            nombres = ", ".join(f"id={d.id}" for d in duplicados)
            log.info(f"  {sobreviviente.nombre!r}: se queda id={sobreviviente.id} "
                     f"(sofa={sobreviviente.sofascore_id}), se fusiona {nombres}")
            if not solo_listar:
                total += fusionar(db, sobreviviente, duplicados)
        if not solo_listar:
            log.info(f"Referencias de partidos repuntadas: {total}")
        return len(grupos)
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    correr_fusion(solo_listar="--listar" in sys.argv)
