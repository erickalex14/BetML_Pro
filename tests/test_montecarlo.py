"""Tests de Monte Carlo — probabilidades tienen que sumar 1, Dixon-Coles
tiene que mover la distribución en la dirección correcta."""
import numpy as np
from backend.models.montecarlo import simular_partido, _grid_marcadores, cargar_rho


def test_1x2_suma_uno():
    r = simular_partido(1.8, 0.9, n_simulaciones=20000)
    suma = r["prob_local"] + r["prob_empate"] + r["prob_visitante"]
    assert abs(suma - 1.0) < 0.01


def test_grid_normalizada_y_sin_negativos():
    rho = cargar_rho()
    g = _grid_marcadores(1.5, 1.2, rho)
    assert abs(g.sum() - 1.0) < 1e-9
    assert (g >= 0).all()


def test_dixon_coles_direccion_correcta():
    rho = cargar_rho()
    assert rho < 0, "rho debería ser negativo (literatura y ajuste empírico coinciden en el signo)"
    g_dc = _grid_marcadores(1.5, 1.2, rho)
    g_indep = _grid_marcadores(1.5, 1.2, 0.0)
    assert g_dc[0, 0] > g_indep[0, 0]  # 0-0 más probable con correlación
    assert g_dc[1, 1] > g_indep[1, 1]  # 1-1 más probable
    assert g_dc[1, 0] < g_indep[1, 0]  # 1-0 menos probable
    assert g_dc[0, 1] < g_indep[0, 1]  # 0-1 menos probable


def test_corners_y_tarjetas_opcionales():
    sin_extra = simular_partido(1.5, 1.5, n_simulaciones=5000)
    assert "corners" not in sin_extra and "tarjetas" not in sin_extra

    con_extra = simular_partido(1.5, 1.5, n_simulaciones=5000,
                                 corners_local=5.0, corners_visit=4.0,
                                 amarillas_local=2.0, amarillas_visit=2.0)
    assert "corners" in con_extra and "tarjetas" in con_extra


def test_handicap_lineas_enteras_permiten_push_medias_no():
    r = simular_partido(1.8, 0.9, n_simulaciones=20000, incluir_handicap=True)
    h_entera = r["handicap"]["0_0"]
    assert h_entera["push"] > 0
    suma = h_entera["gana_local"] + h_entera["push"] + h_entera["gana_visitante"]
    assert abs(suma - 1.0) < 0.01

    h_media = r["handicap"]["m0_5"]
    assert h_media["push"] == 0


def test_primer_tiempo_suma_uno_y_tiene_menos_goles_que_el_total():
    r = simular_partido(1.8, 0.9, n_simulaciones=20000, incluir_ht=True)
    pt = r["primer_tiempo"]
    suma_1t = sum(pt["resultado_1t"].values())
    assert abs(suma_1t - 1.0) < 0.01
    assert pt["prom_goles_1t"] < r["prom_goles_total"]


def test_escenarios_crudos_consistentes_con_agregados():
    r = simular_partido(1.8, 0.9, n_simulaciones=5000,
                         corners_local=5.5, corners_visit=4.0,
                         devolver_escenarios=True)
    esc = r["_escenarios"]
    assert len(esc["goles_local"]) == 5000
    assert abs(np.mean(esc["corners_total"]) - r["corners"]["promedio_total"]) < 0.01
