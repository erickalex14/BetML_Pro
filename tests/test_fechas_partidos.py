from datetime import date, datetime

from backend.db.database import SessionLocal
from backend.db.modelos import Equipo, Liga, Partido
from backend.pipeline.config import rango_utc_dia_partidos
from backend.repositories.partido_repo import PartidoRepository


def test_rango_ecuador_se_convierte_a_utc():
    inicio, fin = rango_utc_dia_partidos(date(2026, 8, 14))
    assert inicio == datetime(2026, 8, 14, 5, 0)
    assert fin == datetime(2026, 8, 15, 5, 0)


def test_get_por_fecha_excluye_noche_anterior_en_utc():
    db = SessionLocal()
    try:
        if db.get(Liga, 99001) is None:
            db.add(Liga(id=99001, nombre="Liga frontera", temporada=2026))
        for equipo_id in (99001, 99002):
            if db.get(Equipo, equipo_id) is None:
                db.add(Equipo(id=equipo_id, nombre=f"Equipo {equipo_id}"))
        db.commit()

        casos = (
            (990001, datetime(2026, 8, 14, 4, 59, 59)),
            (990002, datetime(2026, 8, 14, 5, 0, 0)),
            (990003, datetime(2026, 8, 15, 4, 59, 59)),
            (990004, datetime(2026, 8, 15, 5, 0, 0)),
        )
        for partido_id, fecha in casos:
            partido = db.get(Partido, partido_id)
            if partido is None:
                db.add(Partido(id=partido_id, liga_id=99001, temporada=2026,
                               equipo_local_id=99001, equipo_visit_id=99002,
                               fecha=fecha, estado="NS"))
        db.commit()

        ids = {p.id for p in PartidoRepository(db).get_por_fecha(date(2026, 8, 14))}
        assert 990001 not in ids
        assert 990002 in ids
        assert 990003 in ids
        assert 990004 not in ids
    finally:
        db.close()
