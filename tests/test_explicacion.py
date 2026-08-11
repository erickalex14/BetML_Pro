"""generar_resumen es texto puro sobre números ya calculados — sin DB,
sin modelo cargado. Cubre: orden por importancia, feature invertido
(menor es mejor), caso parejo, y h2h."""
from backend.models.explicacion import generar_resumen, generar_resumen_h2h


def test_ordena_por_importancia_real():
    features = {
        "forma_local_puntos": 12, "forma_visit_puntos": 4,
        "xg_favor_local": 1.0, "xg_favor_visit": 1.0,  # parejo, no debería aparecer primero
    }
    importancias = {"forma_local_puntos": 0.3, "forma_visit_puntos": 0.3,
                     "xg_favor_local": 0.05, "xg_favor_visit": 0.05}

    factores = generar_resumen(features, importancias, "Boca", "River", top_n=2)

    assert factores[0]["factor"] == "forma reciente"
    assert factores[0]["favorece"] == "local"
    assert "Boca" in factores[0]["texto"]


def test_feature_invertido_menor_gana():
    # forma_local_gc (goles recibidos) es invertido: MENOS es mejor
    features = {"forma_local_gc": 2, "forma_visit_gc": 9}
    importancias = {"forma_local_gc": 0.5, "forma_visit_gc": 0.5}

    factores = generar_resumen(features, importancias, "Boca", "River", top_n=1)

    assert factores[0]["favorece"] == "local"  # menos goles recibidos = mejor


def test_caso_parejo_no_fuerza_ganador():
    features = {"win_rate_local": 0.50, "win_rate_visit": 0.505}
    importancias = {"win_rate_local": 0.4, "win_rate_visit": 0.4}

    factores = generar_resumen(features, importancias, "Boca", "River", top_n=1)

    assert factores[0]["favorece"] == "parejo"


def test_h2h_resumen_texto():
    features = {"h2h_wins_local": 3, "h2h_empates": 1, "h2h_wins_visit": 1}
    texto = generar_resumen_h2h(features, "Boca", "River")
    assert texto is not None
    assert "Boca" in texto and "River" in texto
    assert "3" in texto


def test_h2h_sin_historial_devuelve_none():
    assert generar_resumen_h2h({"h2h_wins_local": 0, "h2h_empates": 0, "h2h_wins_visit": 0},
                                "Boca", "River") is None
    assert generar_resumen_h2h({}, "Boca", "River") is None
