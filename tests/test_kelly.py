"""Tests del núcleo de Kelly — la lógica que decide cuánto plata apostar
no puede tener bugs silenciosos. Estos son los mismos checks que se
corrieron a mano durante el desarrollo, formalizados."""
import pytest
from backend.models.kelly import calcular_kelly, analizar_mercados_kelly, construir_lista_mercados
from backend.models.montecarlo import simular_partido
from backend.models.kelly_portfolio import kelly_portfolio, probabilidad_ruina
from backend.models.parlay import calcular_prediccion_combinada, calcular_parlay_kelly


def test_kelly_value_bet_positivo():
    r = calcular_kelly(0.55, 2.10, fraccion=0.25)
    assert r["es_value_bet"] is True
    assert r["stake_kelly"] > 0
    assert r["stake_kelly"] <= 0.05  # nunca pasa el cap individual


def test_kelly_sin_valor_no_apuesta():
    r = calcular_kelly(0.30, 2.10)
    assert r["es_value_bet"] is False
    assert r["stake_kelly"] == 0.0


def test_kelly_entradas_invalidas_no_explota():
    assert calcular_kelly(0, 2.0)["es_value_bet"] is False
    assert calcular_kelly(1, 2.0)["es_value_bet"] is False
    assert calcular_kelly(0.5, 1.0)["es_value_bet"] is False
    assert calcular_kelly(0.5, 0.5)["es_value_bet"] is False


def test_factor_confianza_reduce_stake_sin_cambiar_value_bet():
    normal = calcular_kelly(0.55, 2.10, fraccion=0.25, factor_confianza=1.0)
    reducido = calcular_kelly(0.55, 2.10, fraccion=0.25, factor_confianza=0.5)
    assert reducido["stake_kelly"] < normal["stake_kelly"]
    assert reducido["es_value_bet"] == normal["es_value_bet"] is True


def test_analizar_mercados_solo_1x2_sin_montecarlo():
    pred = {"prob_local": 0.55, "prob_empate": 0.25, "prob_visitante": 0.20}
    odds = {"odds_local": 2.10, "odds_empate": 3.40, "odds_visitante": 4.50}
    r = analizar_mercados_kelly(pred, odds, bankroll=1000)
    assert len(r["todos_mercados"]) == 3


def test_analizar_mercados_extendido_con_montecarlo():
    pred = {"prob_local": 0.55, "prob_empate": 0.25, "prob_visitante": 0.20}
    mc = simular_partido(1.8, 0.9, n_simulaciones=20000,
                          corners_local=5.5, corners_visit=4.0,
                          amarillas_local=2.0, amarillas_visit=2.3)
    odds = {
        "odds_local": 1.90, "odds_empate": 3.60, "odds_visitante": 5.20,
        "odds_goles_over_2_5": 1.85, "odds_btts_si": 1.75,
        "odds_corners_over_9_5": 1.90, "odds_tarjetas_over_2_5": 1.80,
    }
    r = analizar_mercados_kelly(pred, odds, bankroll=1000, montecarlo=mc)
    assert len(r["todos_mercados"]) > 3


def test_kelly_portfolio_correlacionado_no_excede_suma_ingenua():
    mc = simular_partido(1.8, 0.9, n_simulaciones=50000, devolver_escenarios=True)
    esc = mc["_escenarios"]
    gl, gv = esc["goles_local"], esc["goles_visit"]
    gana_local = gl > gv
    gana_over25 = (gl + gv) > 2.5

    mercados = [
        {"nombre": "1X2 Local", "gana_escenario": gana_local, "cuota": 1.90},
        {"nombre": "Over 2.5", "gana_escenario": gana_over25, "cuota": 1.85},
    ]
    port = kelly_portfolio(mercados, fraccion=0.25)

    k1 = calcular_kelly(float(gana_local.mean()), 1.90, fraccion=0.25)
    k2 = calcular_kelly(float(gana_over25.mean()), 1.85, fraccion=0.25)
    suma_ingenua = k1["stake_kelly"] * 100 + k2["stake_kelly"] * 100

    assert port["stake_total_pct"] <= suma_ingenua + 0.5


def test_probabilidad_ruina_escala_con_el_stake():
    mc = simular_partido(1.8, 0.9, n_simulaciones=20000, devolver_escenarios=True)
    gl, gv = mc["_escenarios"]["goles_local"], mc["_escenarios"]["goles_visit"]
    mercados = [{"nombre": "1X2 Local", "gana_escenario": gl > gv, "cuota": 1.90}]

    r_chico = probabilidad_ruina(mercados, [2], n_simulaciones_ruina=1000)
    r_grande = probabilidad_ruina(mercados, [40], n_simulaciones_ruina=1000)
    assert r_grande > r_chico


def test_prediccion_combinada_es_producto_de_probabilidades():
    sels = [
        {"partido_id": 1, "mercado": "1X2 Local", "prob": 0.55, "cuota": 1.90},
        {"partido_id": 2, "mercado": "1X2 Visitante", "prob": 0.40, "cuota": 2.50},
    ]
    r = calcular_prediccion_combinada(sels)
    assert r["prob_combinada"] == pytest.approx(0.55 * 0.40, abs=1e-6)


def test_parlay_kelly_coincide_con_kelly_directo_sobre_valores_combinados():
    sels = [
        {"partido_id": 1, "mercado": "A", "prob": 0.55, "cuota": 1.90},
        {"partido_id": 2, "mercado": "B", "prob": 0.40, "cuota": 2.50},
    ]
    parlay = calcular_parlay_kelly(sels, bankroll=1000, fraccion=0.25)
    directo = calcular_kelly(0.55 * 0.40, 1.90 * 2.50, fraccion=0.25)
    assert parlay["kelly"]["stake_kelly"] == pytest.approx(directo["stake_kelly"], abs=1e-6)


def test_parlay_rechaza_menos_de_dos_selecciones():
    r = calcular_parlay_kelly([{"partido_id": 1, "mercado": "A", "prob": 0.5, "cuota": 2.0}])
    assert "error" in r
