"""con_prediccion era un parámetro muerto (bug real encontrado en sesión:
/partidos/hoy nunca embebía predicción, /partidos/{id} devolvía el ORM
crudo sin nombres de equipo) — estos tests cubren que ambos caminos
efectivamente enriquecen la respuesta ahora."""
from backend.db.database import SessionLocal
from backend.db.modelos import Partido
from backend.services.partido_service import PartidoService


def _un_partido():
    db = SessionLocal()
    p = db.query(Partido).order_by(Partido.fecha.desc()).first()
    return db, p


def test_get_detalle_incluye_nombres_reales_no_ids():
    db, p = _un_partido()
    try:
        data = PartidoService(db).get_detalle(p.id)
        assert data is not None
        assert "local" in data and isinstance(data["local"], str)
        assert data["local"] != "Local"  # no es el fallback del frontend
        assert "prediccion" in data  # clave presente, aunque sea None
    finally:
        db.close()


def test_get_detalle_partido_inexistente_devuelve_none():
    db, _ = _un_partido()
    try:
        assert PartidoService(db).get_detalle(-1) is None
    finally:
        db.close()


def test_get_partidos_hoy_cada_fila_trae_clave_prediccion():
    db, _ = _un_partido()
    try:
        resultado = PartidoService(db).get_partidos_hoy()
        for fila in resultado["partidos"]:
            assert "prediccion" in fila
    finally:
        db.close()
