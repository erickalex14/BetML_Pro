"""Dos fuentes escriben sobre la misma fila de Partido (API-Football en
guardador.py, Sofascore en job_sofascore_en_vivo.py) y no siempre
coinciden. Estos tests fijan la regla de que la peor no pisa a la mejor.

Caso real que los motivó (2026-08-12): Valencia U21 vs Teruel tenía 0-1
traído por Sofascore, corrió el pipeline de API-Football —que en
amistosos chicos se queda en "NS" con goles en null durante horas— y el
marcador se borró: el partido volvió a mostrarse como "por jugarse"."""
from datetime import datetime

from backend.db.database import SessionLocal
from backend.db.modelos import Partido, Equipo
from backend.pipeline.guardador import guardar_partido

PARTIDO_ID = 960001


def _fixture(estado: str, goles_local, goles_visit) -> dict:
    """Payload de API-Football con lo mínimo que lee guardar_partido."""
    return {
        "fixture": {"id": PARTIDO_ID, "date": "2026-08-12T12:00:00+00:00",
                     "status": {"short": estado, "elapsed": None}},
        "league": {"round": "Amistoso"},
        "teams": {"home": {"id": 960010, "name": "Equipo Guardador A", "logo": None},
                   "away": {"id": 960011, "name": "Equipo Guardador B", "logo": None}},
        "goals": {"home": goles_local, "away": goles_visit},
        "score": {"halftime": {"home": None, "away": None}},
    }


def _limpiar(db):
    db.query(Partido).filter(Partido.id == PARTIDO_ID).delete()
    for eid in (960010, 960011):
        db.query(Equipo).filter(Equipo.id == eid).delete()
    db.commit()


def test_no_borra_el_marcador_cuando_la_otra_fuente_no_lo_tiene():
    db = SessionLocal()
    try:
        _limpiar(db)
        guardar_partido(db, _fixture("FT", 0, 1), liga_id=667, temporada=2026)

        # la otra fuente todavia lo ve sin jugar y sin goles
        guardar_partido(db, _fixture("NS", None, None), liga_id=667, temporada=2026)

        p = db.get(Partido, PARTIDO_ID)
        assert p.goles_local == 0 and p.goles_visitante == 1
        assert p.estado == "FT"   # no retrocede a "por jugarse"
    finally:
        _limpiar(db)
        db.close()


def test_si_actualiza_cuando_la_fuente_trae_datos_de_verdad():
    db = SessionLocal()
    try:
        _limpiar(db)
        guardar_partido(db, _fixture("1H", 0, 0), liga_id=667, temporada=2026)
        guardar_partido(db, _fixture("FT", 2, 1), liga_id=667, temporada=2026)

        p = db.get(Partido, PARTIDO_ID)
        assert (p.estado, p.goles_local, p.goles_visitante) == ("FT", 2, 1)
    finally:
        _limpiar(db)
        db.close()
