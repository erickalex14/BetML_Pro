import logging
from typing import Optional

log = logging.getLogger(__name__)


def calcular_kelly(
    probabilidad_modelo: float,
    cuota_decimal: float,
    fraccion: float = 0.25
) -> dict:
    """
    Calcula el stake óptimo usando el Criterio de Kelly Fraccionario.

    Parámetros:
      probabilidad_modelo → prob del modelo para esta selección (0-1)
      cuota_decimal       → cuota del bookmaker (ej: 2.10)
      fraccion            → fracción de Kelly a usar (default 0.25)
                            Kelly completo = 1.0 (muy agresivo)
                            Kelly cuarto   = 0.25 (conservador)

    Fórmula Kelly:
      f* = (b × p - q) / b
      donde:
        b = cuota neta (cuota_decimal - 1)
        p = probabilidad del modelo
        q = 1 - p (probabilidad de perder)

    Retorna:
      stake_kelly    → fracción del bankroll a apostar
      ev             → valor esperado de la apuesta
      es_value_bet   → True si EV > 0 (apuesta con valor)
      cuota_justa    → la cuota que debería ser según el modelo
    """
    if probabilidad_modelo <= 0 or probabilidad_modelo >= 1:
        return _resultado_vacio("Probabilidad inválida")

    if cuota_decimal <= 1.0:
        return _resultado_vacio("Cuota inválida — debe ser > 1.0")

    # Cuota neta (ganancia neta por unidad apostada)
    b = cuota_decimal - 1.0

    # Probabilidad de perder
    q = 1.0 - probabilidad_modelo

    # Kelly completo
    kelly_completo = (b * probabilidad_modelo - q) / b

    # Si Kelly es negativo → no hay valor en esta apuesta
    if kelly_completo <= 0:
        return {
            "stake_kelly":   0.0,
            "kelly_completo":round(kelly_completo, 4),
            "ev":            round((b * probabilidad_modelo - q), 4),
            "es_value_bet":  False,
            "cuota_justa":   round(1 / probabilidad_modelo, 2),
            "prob_implicita":round(1 / cuota_decimal, 4),
            "edge":          round(probabilidad_modelo - (1/cuota_decimal), 4),
            "mensaje":       "Sin valor — no apostar"
        }

    # Kelly fraccionario — reduce volatilidad
    stake_kelly = kelly_completo * fraccion

    # Limita el stake máximo al 5% del bankroll
    # protege contra errores del modelo
    stake_kelly = min(stake_kelly, 0.05)

    # Valor esperado: cuánto ganas en promedio por unidad apostada
    ev = b * probabilidad_modelo - q

    # Probabilidad implícita de la cuota del bookmaker
    prob_implicita = 1 / cuota_decimal

    # Edge: ventaja del modelo sobre el mercado
    edge = probabilidad_modelo - prob_implicita

    return {
        "stake_kelly":    round(stake_kelly, 4),
        "kelly_completo": round(kelly_completo, 4),
        "ev":             round(ev, 4),
        "es_value_bet":   True,
        "cuota_justa":    round(1 / probabilidad_modelo, 2),
        "prob_implicita": round(prob_implicita, 4),
        "edge":           round(edge, 4),
        "mensaje":        f"Apostar {stake_kelly*100:.1f}% del bankroll"
    }


def analizar_mercados_kelly(
    prediccion: dict,
    odds: dict,
    bankroll: float = 1000.0,
    fraccion: float = 0.25
) -> list:
    """
    Analiza todos los mercados de un partido y calcula
    el stake óptimo para cada uno usando Kelly.

    Parámetros:
      prediccion → dict con prob_local, prob_empate, prob_visitante
      odds       → dict con odds_local, odds_empate, odds_visitante
      bankroll   → capital disponible en la moneda que uses
      fraccion   → fracción de Kelly (default 0.25)

    Retorna lista de mercados ordenados por EV descendente.
    """
    mercados = []

    # Mapeo de mercado → probabilidad del modelo → cuota
    analisis = [
        ("1X2 Local",     prediccion.get("prob_local",      0),
                          odds.get("odds_local",            0)),
        ("1X2 Empate",    prediccion.get("prob_empate",      0),
                          odds.get("odds_empate",           0)),
        ("1X2 Visitante", prediccion.get("prob_visitante",   0),
                          odds.get("odds_visitante",        0)),
    ]

    for nombre_mercado, prob, cuota in analisis:
        if cuota <= 1.0 or prob <= 0:
            continue

        kelly = calcular_kelly(prob, cuota, fraccion)

        stake_unidades = kelly["stake_kelly"] * bankroll

        mercados.append({
            "mercado":        nombre_mercado,
            "probabilidad":   round(prob, 4),
            "cuota":          round(cuota, 2),
            "ev":             kelly["ev"],
            "edge":           kelly["edge"],
            "es_value_bet":   kelly["es_value_bet"],
            "stake_pct":      round(kelly["stake_kelly"] * 100, 2),
            "stake_units":    round(stake_unidades, 2),
            "cuota_justa":    kelly["cuota_justa"],
            "prob_implicita": kelly["prob_implicita"],
            "mensaje":        kelly["mensaje"],
        })

    # Ordena por EV descendente — las mejores apuestas primero
    mercados.sort(key=lambda x: x["ev"], reverse=True)

    # Filtra solo value bets
    value_bets = [m for m in mercados if m["es_value_bet"]]

    return {
        "todos_mercados": mercados,
        "value_bets":     value_bets,
        "n_value_bets":   len(value_bets),
        "bankroll":       bankroll,
        "fraccion_kelly": fraccion,
    }


def _resultado_vacio(mensaje: str) -> dict:
    return {
        "stake_kelly":    0.0,
        "kelly_completo": 0.0,
        "ev":             0.0,
        "es_value_bet":   False,
        "cuota_justa":    0.0,
        "prob_implicita": 0.0,
        "edge":           0.0,
        "mensaje":        mensaje
    }


def simular_estrategias(
    historial: list,
    bankroll_inicial: float = 1000.0
) -> dict:
    """
    Compara Kelly vs Stake Fijo en datos históricos.

    historial → lista de dicts con:
      prob_modelo, cuota, resultado (1=ganó, 0=perdió)

    Retorna métricas de cada estrategia para el CV/dashboard.
    """
    bankroll_kelly = bankroll_inicial
    bankroll_fijo  = bankroll_inicial
    stake_fijo_pct = 0.02  # 2% fijo del bankroll inicial

    resultados_kelly = []
    resultados_fijo  = []

    for apuesta in historial:
        prob   = apuesta["prob_modelo"]
        cuota  = apuesta["cuota"]
        gano   = apuesta["resultado"]

        # Kelly
        k = calcular_kelly(prob, cuota)
        stake_k = k["stake_kelly"] * bankroll_kelly

        if gano:
            bankroll_kelly += stake_k * (cuota - 1)
        else:
            bankroll_kelly -= stake_k

        resultados_kelly.append(bankroll_kelly)

        # Stake fijo
        stake_f = stake_fijo_pct * bankroll_inicial
        if gano:
            bankroll_fijo += stake_f * (cuota - 1)
        else:
            bankroll_fijo -= stake_f

        resultados_fijo.append(bankroll_fijo)

    roi_kelly = (bankroll_kelly - bankroll_inicial) / bankroll_inicial * 100
    roi_fijo  = (bankroll_fijo  - bankroll_inicial) / bankroll_inicial * 100

    return {
        "kelly": {
            "bankroll_final": round(bankroll_kelly, 2),
            "roi_pct":        round(roi_kelly, 2),
            "curva":          resultados_kelly,
        },
        "fijo": {
            "bankroll_final": round(bankroll_fijo, 2),
            "roi_pct":        round(roi_fijo, 2),
            "curva":          resultados_fijo,
        }
    }