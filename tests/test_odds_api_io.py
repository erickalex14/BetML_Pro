"""Parser de odds-api.io — datos calcados de la respuesta real para
Tobol Kostanay vs FK Partizan (evento 73011680, 13/08/2026).

Lo que se cuida acá: que BETANO tenga prioridad sobre las demas casas.
El usuario apuesta en Betano, asi que una cuota mejor en otra casa
inflaria el EV de una apuesta que no puede hacer."""
from backend.pipeline.odds.odds_api_io import parsear_bookmakers, _decimal, _linea


def test_decimal_y_linea():
    assert _decimal("3.250") == 3.25
    assert _decimal("1.000") is None      # no paga nada
    assert _decimal(None) is None
    assert _linea(2.5) == "2_5"
    assert _linea(-1.25) == "m1_25"


def test_betano_manda_sobre_bet365_en_el_mismo_mercado():
    bookmakers = {
        "Bet365": [{"name": "ML", "odds": [{"home": "3.250", "draw": "2.200", "away": "3.200"}]}],
        "Betano": [{"name": "ML", "odds": [{"home": "3.15", "draw": "2.18", "away": "3.30"}]}],
    }
    r = parsear_bookmakers(bookmakers)
    # gana Betano aunque Bet365 pague MAS en el local: es donde se apuesta
    assert r["odds_local"] == 3.15
    assert r["odds_empate"] == 2.18
    assert r["odds_visitante"] == 3.30


def test_usa_bet365_cuando_betano_no_cotiza_ese_mercado():
    bookmakers = {
        "Bet365": [{"name": "Corners Totals", "odds": [{"hdp": 9.5, "over": "1.80", "under": "2.00"}]}],
        "Betano": [{"name": "ML", "odds": [{"home": "3.15", "draw": "2.18", "away": "3.30"}]}],
    }
    r = parsear_bookmakers(bookmakers)
    assert r["odds_local"] == 3.15                  # de Betano
    assert r["odds_corners_over_9_5"] == 1.8        # de Bet365, Betano no lo trae


def test_totals_y_btts_con_la_linea_en_hdp():
    bookmakers = {"Betano": [
        {"name": "Totals", "odds": [
            {"hdp": 2.5, "over": "1.400", "under": "2.850"},
            {"hdp": 3.5, "over": "2.70", "under": "1.42"}]},
        {"name": "Both Teams To Score", "odds": [{"yes": "1.57", "no": "2.25"}]},
    ]}
    r = parsear_bookmakers(bookmakers)
    assert r["odds_goles_over_2_5"] == 1.4
    assert r["odds_goles_under_3_5"] == 1.42
    assert r["odds_btts_si"] == 1.57
    assert r["odds_btts_no"] == 2.25


def test_spread_guarda_la_linea_simetrica_para_el_visitante():
    bookmakers = {"Betano": [{"name": "Spread", "odds": [
        {"hdp": -0.5, "home": "3.100", "away": "1.350"}]}]}
    r = parsear_bookmakers(bookmakers)
    assert r["odds_handicap_local_m0_5"] == 3.1
    assert r["odds_handicap_visit_0_5"] == 1.35
