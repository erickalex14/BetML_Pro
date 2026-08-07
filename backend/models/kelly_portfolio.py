"""Kelly de portafolio — para cuando se apuesta a VARIOS mercados del
MISMO partido a la vez (ej: 1X2 Local + Over2.5 + BTTS-No).

calcular_kelly() en kelly.py trata cada apuesta como independiente, pero
no lo son: si el visitante gana por goleada, 1X2 Local pierde Y BTTS-No
puede perder también (si el local también anotó) — el riesgo no se
diversifica tanto como la suma de los Kelly individuales asume. Kelly de
portafolio optimiza el vector de stakes considerando la correlación
real, tomada directamente de las simulaciones Monte Carlo conjuntas
(cada escenario ya tiene el resultado de TODOS los mercados a la vez —
no hace falta estimar una matriz de covarianza aparte).

También agrega un límite de riesgo de ruina: simula la curva de bankroll
resultante de apostar esta combinación repetidamente y mide qué tan
seguido cae por debajo de un umbral crítico.
"""
import logging
import numpy as np
from scipy.optimize import minimize

log = logging.getLogger(__name__)

CAP_INDIVIDUAL = 0.05  # mismo tope que calcular_kelly, por apuesta
CAP_TOTAL_PORTAFOLIO = 0.15  # tope combinado — no todo el bankroll en un partido


def kelly_portfolio(mercados: list, fraccion: float = 0.25,
                     cap_individual: float = CAP_INDIVIDUAL,
                     cap_total: float = CAP_TOTAL_PORTAFOLIO) -> dict:
    """
    mercados: [{"nombre": str, "gana_escenario": np.ndarray[bool] (n,),
                "cuota": float}, ...] — todas del MISMO partido, mismo n
                de escenarios (salen de simular_partido(devolver_escenarios=True)).
    fraccion: fracción de Kelly a aplicar sobre el óptimo matemático
              (mismo rol que en calcular_kelly — 0.25 = Kelly cuarto).

    Devuelve stake por mercado + crecimiento esperado del portafolio.
    Mercados sin edge positivo individual quedan en stake=0 (el
    optimizador los excluye solo, no hace falta filtrarlos antes).
    """
    n_mercados = len(mercados)
    if n_mercados == 0:
        return {"mercados": [], "ev_portafolio": 0.0}

    n_escenarios = len(mercados[0]["gana_escenario"])
    gana = np.array([m["gana_escenario"] for m in mercados])  # (n_mercados, n_escenarios)
    b = np.array([m["cuota"] - 1.0 for m in mercados])  # cuota neta por mercado

    def neg_log_crecimiento(f):
        # payoff por escenario: +f_i*b_i si ganó, -f_i si perdió
        payoff = np.where(gana, f[:, None] * b[:, None], -f[:, None])
        crecimiento = 1.0 + payoff.sum(axis=0)  # (n_escenarios,) — riqueza relativa por escenario
        crecimiento = np.clip(crecimiento, 1e-6, None)  # evita log(negativo) si f es agresivo
        return -np.mean(np.log(crecimiento))

    restricciones = [{"type": "ineq", "fun": lambda f: cap_total - f.sum()}]
    limites = [(0.0, cap_individual)] * n_mercados
    f0 = np.full(n_mercados, min(cap_individual, cap_total / max(n_mercados, 1)) / 2)

    resultado_opt = minimize(
        neg_log_crecimiento, f0, method="SLSQP",
        bounds=limites, constraints=restricciones,
    )

    f_optimo = np.clip(resultado_opt.x, 0, None) * fraccion

    payoff_final = np.where(gana, f_optimo[:, None] * b[:, None], -f_optimo[:, None])
    crecimiento_final = 1.0 + payoff_final.sum(axis=0)
    ev_portafolio = float(np.mean(crecimiento_final) - 1.0)

    salida = []
    for i, m in enumerate(mercados):
        prob_empirica = float(np.mean(gana[i]))
        salida.append({
            "mercado": m["nombre"],
            "cuota": round(m["cuota"], 2),
            "probabilidad": round(prob_empirica, 4),
            "stake_pct": round(float(f_optimo[i]) * 100, 2),
        })

    return {
        "mercados": salida,
        "stake_total_pct": round(float(f_optimo.sum()) * 100, 2),
        "ev_portafolio": round(ev_portafolio, 4),
        "n_escenarios": n_escenarios,
    }


def probabilidad_ruina(mercados: list, stakes_pct: list, bankroll_inicial: float = 1000.0,
                        n_apuestas_secuencia: int = 50, n_simulaciones_ruina: int = 2000,
                        umbral_ruina: float = 0.5) -> float:
    """
    Simula qué pasa si esta MISMA combinación de apuestas (mismos stakes)
    se repite n_apuestas_secuencia veces seguidas (aproximación de una
    temporada de apostar el mismo tipo de portafolio cada fin de semana),
    usando las probabilidades empíricas de cada mercado. Devuelve la
    fracción de esas simulaciones donde el bankroll cae por debajo de
    umbral_ruina * bankroll_inicial en algún punto del camino.

    No reusa los mismos escenarios de Monte Carlo del partido — esto
    simula SECUENCIAS de partidos distintos con las mismas probabilidades,
    no el mismo partido repetido.
    """
    probs = np.array([float(np.mean(m["gana_escenario"])) for m in mercados])
    cuotas = np.array([m["cuota"] for m in mercados])
    stakes = np.array(stakes_pct) / 100.0

    bankrolls = np.full(n_simulaciones_ruina, bankroll_inicial)
    cayo_bajo_umbral = np.zeros(n_simulaciones_ruina, dtype=bool)

    rng = np.random.default_rng(42)
    for _ in range(n_apuestas_secuencia):
        resultados = rng.random((n_simulaciones_ruina, len(mercados))) < probs
        cambio = np.where(
            resultados,
            stakes * (cuotas - 1.0),
            -stakes,
        ).sum(axis=1)
        bankrolls = bankrolls * (1.0 + cambio)
        bankrolls = np.clip(bankrolls, 0, None)
        cayo_bajo_umbral |= (bankrolls < umbral_ruina * bankroll_inicial)

    return round(float(np.mean(cayo_bajo_umbral)), 4)
