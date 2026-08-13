"""El sistema aprende de sus aciertos y errores, en TODOS los mercados
y con las predicciones de TODOS los usuarios.

Los tests van contra la lógica pura (clasificación de mercados y el
cálculo del factor), sin tocar la base: el .env de desarrollo apunta a
la base de PRODUCCIÓN por el túnel, así que una suite que inserte filas
estaría ensuciando datos reales — y ademas el resultado dependeria de
cuantas predicciones haya ese dia.
"""
from backend.models.calibracion_produccion import (
    calcular_factor, corregir, familia_de,
    FACTOR_MIN, FACTOR_MAX, K_ENCOGIMIENTO,
)


def test_cada_mercado_va_a_su_propia_familia():
    """El error de corners no puede arrastrar al 1X2: cada mecanica se
    corrige por separado."""
    assert familia_de("corners_over_9_5") == "corners"
    assert familia_de("btts_si") == "btts"
    assert familia_de("handicap_local_m1_5") == "handicap"
    assert familia_de("local") == "1x2"
    assert familia_de("tarjetas_over_2_5") == "tarjetas"
    assert familia_de("rojas_over_0_5") == "rojas"
    assert familia_de("goles_equipo_local_over_1_5") == "goles_equipo"
    assert familia_de("goles_over_2_5") == "goles"
    # el orden importa: los goles del PRIMER TIEMPO no son los del partido
    assert familia_de("goles_1t_over_0_5") == "goles_1t"
    assert familia_de("1t_local") == "resultado_1t"
    assert familia_de("2t_empate") == "resultado_2t"


def test_con_poca_muestra_corrige_poco():
    """Fallar 8 de 8 no puede hundir la probabilidad: con esa muestra la
    frecuencia observada es ruido."""
    factor = calcular_factor(n=8, declarado=0.80, real=0.0)
    assert 0.65 < factor < 1.0, factor


def test_con_mucha_muestra_manda_lo_observado():
    """Con 200 observaciones diciendo que declaramos 60% y acertamos
    20%, hay que hacerle caso (hasta el tope)."""
    factor = calcular_factor(n=200, declarado=0.60, real=0.20)
    assert factor == FACTOR_MIN  # llega al tope de seguridad
    # y sin tope estaria cerca de real/declarado
    crudo = (200 * 0.20 + K_ENCOGIMIENTO * 0.60) / ((220) * 0.60)
    assert crudo < 0.5


def test_si_venimos_pesimistas_sube_la_probabilidad():
    """Tambien aprende del lado bueno: si declaramos 30% y acierta el
    50%, el factor pasa de 1."""
    assert calcular_factor(n=100, declarado=0.30, real=0.50) > 1.0


def test_sin_muestra_no_inventa_correccion():
    assert calcular_factor(n=0, declarado=0.5, real=0.0) == 1.0
    assert calcular_factor(n=10, declarado=0.0, real=0.0) == 1.0


def test_los_topes_nunca_anulan_ni_inflan_de_mas():
    assert FACTOR_MIN >= 0.5 and FACTOR_MAX <= 1.3
    assert calcular_factor(n=500, declarado=0.90, real=0.0) == FACTOR_MIN
    assert calcular_factor(n=500, declarado=0.10, real=0.90) == FACTOR_MAX


def test_corregir_aplica_el_factor_de_su_familia_y_nada_mas():
    factores = {"corners": {"factor": 0.7, "n": 50, "declarado": 0.6, "real": 0.1}}
    assert corregir(0.80, "corners_over_9_5", factores) == 0.80 * 0.7
    # otra familia: no se toca
    assert corregir(0.80, "tarjetas_over_2_5", factores) == 0.80
    # sin datos: no se toca
    assert corregir(0.80, "corners_over_9_5", {}) == 0.80
    # nunca se pasa de 1
    assert corregir(0.95, "corners_over_9_5",
                    {"corners": {"factor": 1.3, "n": 50, "declarado": 0.5, "real": 0.9}}) <= 1.0
