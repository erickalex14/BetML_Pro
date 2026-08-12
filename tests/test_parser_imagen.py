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


def test_desambigua_equipo_duplicado_por_nombre():
    """Bug real de sesión: hay 2 filas 'Fluminense' en Equipo (ids
    distintos, nunca deduplicadas) — buscar_candidatos sin liga_id (la
    imagen no trae ese contexto) puede devolver el candidato equivocado
    como top-1. Antes del fix, resolver_partido_y_mercados solo miraba
    ese top-1 y fallaba con "no hay partido en BD" aunque el partido
    real existiera con el OTRO id del mismo nombre. El fix: se guardan
    TODOS los candidatos por encima del umbral y se cruza con Partido
    real vía .in_(), no un id ya fijado de antemano."""
    db = SessionLocal()
    ahora = datetime.now()
    # tiene que caer DENTRO de VENTANA_DIAS_PARTIDO_ACTUAL, si no
    # resolver_partido_y_mercados lo rechaza por "viejo" (otro chequeo,
    # cubierto por el test de arriba) y este test daría falso negativo
    candidatos_fecha = (
        db.query(Partido)
        .filter(Partido.fecha >= ahora - timedelta(days=3), Partido.fecha <= ahora + timedelta(days=3))
        .all()
    )
    partido_real = min(candidatos_fecha, key=lambda p: abs((p.fecha - ahora).total_seconds()))
    id_correcto = partido_real.equipo_local_id
    id_falso = id_correcto + 10_000_000  # id que no corresponde a ningún Partido real

    analisis = {
        "equipos_detectados": [
            # top-1 (equipo_id) es el FALSO — el correcto solo aparece en equipo_ids
            {"texto_original": "a", "equipo_id": id_falso, "equipo_ids": [id_falso, id_correcto],
             "nombre": "Equipo Ambiguo", "score": 0.9},
            {"texto_original": "b", "equipo_id": partido_real.equipo_visit_id,
             "equipo_ids": [partido_real.equipo_visit_id], "nombre": "Rival", "score": 0.9},
        ],
        "selecciones": [{"tipo": "1x2", "equipo_texto": "a"}],
    }

    partido, mercados, avisos = resolver_partido_y_mercados(db, analisis)
    db.close()

    assert partido is not None
    assert partido.id == partido_real.id
    assert mercados[0]["mercado"] == "local"
