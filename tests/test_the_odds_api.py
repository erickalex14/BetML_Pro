"""Parser de The Odds API — datos con la forma exacta que documenta su
guia v4 (bookmakers -> markets -> outcomes con price/point).

Lo delicado: el mercado h2h NO dice cual opcion es local y cual
visitante, vienen los nombres de los equipos, asi que hay que cruzarlos
contra el equipo local del evento. Equivocarse ahi invierte las cuotas
de local y visitante, que en Kelly es plata mal apostada."""
from backend.pipeline.odds.the_odds_api import _parsear_evento, _decimal


def test_decimal_descarta_valores_imposibles():
    assert _decimal(2.5) == 2.5
    assert _decimal("1.85") == 1.85
    assert _decimal(1.0) is None    # una cuota de 1.0 no paga nada
    assert _decimal(0.5) is None
    assert _decimal(None) is None
    assert _decimal("x") is None


def test_h2h_asigna_local_visitante_por_nombre_no_por_orden():
    evento = {
        "home_team": "Arsenal", "away_team": "Chelsea",
        "bookmakers": [{"key": "b1", "markets": [{"key": "h2h", "outcomes": [
            {"name": "Chelsea", "price": 4.0},   # visitante PRIMERO a proposito
            {"name": "Arsenal", "price": 1.8},
            {"name": "Draw", "price": 3.5},
        ]}]}],
    }
    r = _parsear_evento(evento)
    assert r["odds_local"] == 1.8       # Arsenal es local aunque vino segundo
    assert r["odds_visitante"] == 4.0
    assert r["odds_empate"] == 3.5


def test_totals_usa_el_campo_point_como_linea():
    evento = {
        "home_team": "Arsenal", "away_team": "Chelsea",
        "bookmakers": [{"key": "b1", "markets": [{"key": "totals", "outcomes": [
            {"name": "Over", "price": 1.9, "point": 2.5},
            {"name": "Under", "price": 1.95, "point": 2.5},
        ]}]}],
    }
    r = _parsear_evento(evento)
    assert r["odds_goles_over_2_5"] == 1.9
    assert r["odds_goles_under_2_5"] == 1.95


def test_se_queda_con_la_mejor_cuota_entre_bookmakers():
    evento = {
        "home_team": "Arsenal", "away_team": "Chelsea",
        "bookmakers": [
            {"key": "b1", "markets": [{"key": "h2h", "outcomes": [
                {"name": "Arsenal", "price": 1.80}]}]},
            {"key": "b2", "markets": [{"key": "h2h", "outcomes": [
                {"name": "Arsenal", "price": 1.95}]}]},
        ],
    }
    assert _parsear_evento(evento)["odds_local"] == 1.95
