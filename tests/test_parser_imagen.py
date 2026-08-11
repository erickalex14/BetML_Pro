"""Tests de los parsers de texto de parser_imagen.py — la parte rápida
y determinística (regex/heurísticas). El pipeline completo con EasyOCR
(descarga modelos, corre inferencia) se verificó a mano con una imagen
real — no entra en la suite automática para no volverla lenta."""
from datetime import datetime, timedelta
from backend.db.database import SessionLocal
from backend.db.modelos import Partido
from backend.models.parser_imagen import (
    _clasificar_over_under, _es_resultado_partido, _es_btts, _linea_a_clave,
    resolver_partido_y_mercados,
)


def test_over_under_tolera_espacios_comidos_por_ocr():
    assert _clasificar_over_under("Masde 2.5") == {"lado": "over", "linea": 2.5}
    assert _clasificar_over_under("Mas de 2.5") == {"lado": "over", "linea": 2.5}
    assert _clasificar_over_under("Menos de 9.5") == {"lado": "under", "linea": 9.5}
    assert _clasificar_over_under("Over 2.5") == {"lado": "over", "linea": 2.5}


def test_over_under_sin_numero_no_matchea():
    assert _clasificar_over_under("Resultado del partido") is None
    assert _clasificar_over_under("Goles totales") is None


def test_resultado_partido_tolera_ruido_de_ocr():
    assert _es_resultado_partido("Resultado del partido")
    assert _es_resultado_partido("Pesultadodel partido")  # R->P, sin espacio
    assert not _es_resultado_partido("Goles totales")


def test_btts():
    assert _es_btts("Ambos equipos anotan: Sí") == "si"
    assert _es_btts("Both teams to score: No") == "no"
    assert _es_btts("Goles totales") is None


def test_linea_a_clave_coincide_con_montecarlo():
    # mismo formato que montecarlo.py/_linea_a_clave en job_odds.py —
    # necesario para que las claves matcheen entre módulos
    assert _linea_a_clave(2.5) == "2_5"
    assert _linea_a_clave(9.5) == "9_5"


def test_no_usa_partido_viejo_como_si_fuera_el_de_la_imagen():
    """Bug real de sesión: Bodo/Glimt vs Union Saint-Gilloise en la
    imagen era un partido de HOY (clasificatoria Champions 2026), pero
    el único partido de esos equipos en BD era de octubre 2024 — el
    sistema lo usó igual y dio un análisis confiado del partido
    equivocado. Un partido a 677 días de hoy no puede ser "el de la
    imagen" — resolver_partido_y_mercados debe rechazarlo, no usarlo."""
    db = SessionLocal()
    equipo_a = db.query(Partido.equipo_local_id).filter(Partido.estado == "FT").first()[0]
    partido_viejo = (
        db.query(Partido)
        .filter(Partido.equipo_local_id == equipo_a, Partido.estado == "FT")
        .order_by(Partido.fecha.asc())
        .first()
    )
    equipo_b = partido_viejo.equipo_visit_id

    analisis = {
        "equipos_detectados": [
            {"texto_original": "a", "equipo_id": equipo_a, "nombre": "A", "score": 0.9},
            {"texto_original": "b", "equipo_id": equipo_b, "nombre": "B", "score": 0.9},
        ],
        "selecciones": [],
    }

    partido, mercados, avisos = resolver_partido_y_mercados(db, analisis)
    db.close()

    assert partido is None
    assert len(avisos) == 1
    assert "probablemente NO es el de la imagen" in avisos[0]
