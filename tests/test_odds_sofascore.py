"""Parser de cuotas de Sofascore — datos calcados de la respuesta real
de /event/16585849/odds/1/all (FC København vs Debreceni VSC,
2026-08-13). Sin red ni DB.

Lo delicado acá es que el formato NO se parece al de API-Football: las
cuotas vienen fraccionarias ("1/5" es 1.20 decimal, no 0.2) y la línea
del mercado va en un campo aparte ("choiceGroup"), no dentro del nombre
de la opción. Un error en cualquiera de las dos cosas mete cuotas
falsas en el cálculo de Kelly, que es plata."""
from backend.pipeline.sofascore.job_odds_sofascore import _a_decimal, parsear_mercados


def test_convierte_cuota_fraccionaria_a_decimal():
    assert _a_decimal("1/5") == 1.2      # favorito
    assert _a_decimal("19/4") == 5.75
    assert _a_decimal("9/1") == 10.0
    assert _a_decimal("1/1") == 2.0      # cuota pareja
    assert _a_decimal("") is None
    assert _a_decimal(None) is None
    assert _a_decimal("raro") is None
    assert _a_decimal("1/0") is None     # sin division por cero


def test_parsea_1x2_btts_y_lineas_de_goles():
    mercados = [
        {"marketName": "Full time", "suspended": False, "choices": [
            {"name": "1", "fractionalValue": "1/5"},
            {"name": "X", "fractionalValue": "19/4"},
            {"name": "2", "fractionalValue": "9/1"}]},
        {"marketName": "Both teams to score", "suspended": False, "choices": [
            {"name": "Yes", "fractionalValue": "1/1"},
            {"name": "No", "fractionalValue": "8/11"}]},
        {"marketName": "Match goals", "choiceGroup": "2.5", "suspended": False, "choices": [
            {"name": "Over", "fractionalValue": "1/2"},
            {"name": "Under", "fractionalValue": "6/4"}]},
    ]
    r = parsear_mercados(mercados)

    assert r["odds_local"] == 1.2
    assert r["odds_empate"] == 5.75
    assert r["odds_visitante"] == 10.0
    assert r["odds_btts_si"] == 2.0
    assert r["odds_goles_over_2_5"] == 1.5
    assert r["odds_goles_under_2_5"] == 2.5


def test_la_linea_sale_de_choiceGroup_no_del_nombre():
    mercados = [
        {"marketName": "Corners 2-Way", "choiceGroup": "9.5", "suspended": False, "choices": [
            {"name": "Over", "fractionalValue": "4/5"},
            {"name": "Under", "fractionalValue": "1/1"}]},
    ]
    r = parsear_mercados(mercados)
    assert r["odds_corners_over_9_5"] == 1.8
    assert r["odds_corners_under_9_5"] == 2.0


def test_handicap_guarda_la_linea_simetrica_para_el_visitante():
    mercados = [
        {"marketName": "Asian handicap", "choiceGroup": "-1.5", "suspended": False, "choices": [
            {"name": "1", "fractionalValue": "1/1"},
            {"name": "2", "fractionalValue": "4/5"}]},
    ]
    r = parsear_mercados(mercados)
    assert r["odds_handicap_local_m1_5"] == 2.0
    assert r["odds_handicap_visit_1_5"] == 1.8


def test_ignora_mercados_suspendidos_y_los_que_no_modelamos():
    mercados = [
        {"marketName": "Full time", "suspended": True, "choices": [
            {"name": "1", "fractionalValue": "1/5"}]},
        {"marketName": "Draw no bet", "suspended": False, "choices": [
            {"name": "1", "fractionalValue": "1/14"}]},
        {"marketName": "First team to score", "suspended": False, "choices": [
            {"name": "1", "fractionalValue": "8/13"}]},
    ]
    assert parsear_mercados(mercados) == {}
