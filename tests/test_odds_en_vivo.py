"""Parsers puros del feed /odds/live — sin DB, sin red. Cubre: filtro de
mercados suspendidos (no apostables ahora mismo) y armado de clave/línea
desde el campo "handicap" (vocabulario distinto al de /odds pre-partido,
ver docstring de job_odds_en_vivo.py)."""
from backend.pipeline.job_odds_en_vivo import _parsear_over_under_vivo, _sin_suspender, MAPEO_MERCADOS_VIVO


def test_over_under_vivo_arma_clave_desde_handicap():
    valores = [
        {"value": "Over", "odd": "2.375", "handicap": "2.5", "suspended": False},
        {"value": "Under", "odd": "1.55", "handicap": "2.5", "suspended": False},
    ]
    salida = _parsear_over_under_vivo(valores, "goles")
    assert salida == {"odds_goles_over_2_5": 2.375, "odds_goles_under_2_5": 1.55}


def test_over_under_vivo_descarta_suspendidos():
    valores = [
        {"value": "Over", "odd": "1.08", "handicap": "1.5", "suspended": True},
        {"value": "Under", "odd": "7.0", "handicap": "1.5", "suspended": False},
    ]
    salida = _parsear_over_under_vivo(valores, "corners")
    assert "odds_corners_over_1_5" not in salida
    assert salida["odds_corners_under_1_5"] == 7.0


def test_sin_suspender_filtra_y_devuelve_value_odd():
    valores = [
        {"value": "Home", "odd": "1.006", "suspended": True},
        {"value": "Draw", "odd": "29", "suspended": False},
    ]
    assert _sin_suspender(valores) == {"Draw": "29"}


def test_fulltime_result_via_mapeo():
    valores = [
        {"value": "Home", "odd": "1.5", "suspended": False},
        {"value": "Draw", "odd": "4.0", "suspended": False},
        {"value": "Away", "odd": "6.0", "suspended": False},
    ]
    salida = MAPEO_MERCADOS_VIVO["Fulltime Result"](valores)
    assert salida == {"odds_local": 1.5, "odds_empate": 4.0, "odds_visitante": 6.0}


def test_team_goals_via_mapeo_usa_prefijo_goles_equipo():
    valores = [
        {"value": "Over", "odd": "2.62", "handicap": "2.5", "suspended": False},
        {"value": "Under", "odd": "1.44", "handicap": "2.5", "suspended": False},
    ]
    salida = MAPEO_MERCADOS_VIVO["Home Team Goals"](valores)
    assert salida == {"odds_goles_equipo_local_over_2_5": 2.62, "odds_goles_equipo_local_under_2_5": 1.44}
