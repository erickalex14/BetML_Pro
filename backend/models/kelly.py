import logging
from typing import Optional
from backend.models.calibracion import factor_confianza

log = logging.getLogger(__name__)


def calcular_kelly(
    probabilidad_modelo: float,
    cuota_decimal: float,
    fraccion: float = 0.25,
    factor_confianza: float = 1.0,
) -> dict:
    """
    Calcula el stake óptimo usando el Criterio de Kelly Fraccionario.

    Parámetros:
      probabilidad_modelo → prob del modelo para esta selección (0-1),
                            idealmente ya calibrada (ver calibracion.py)
      cuota_decimal       → cuota del bookmaker (ej: 2.10)
      fraccion            → fracción de Kelly a usar (default 0.25)
                            Kelly completo = 1.0 (muy agresivo)
                            Kelly cuarto   = 0.25 (conservador)
      factor_confianza    → multiplica la fracción (0.4-1.0). Baja el
                            stake en rangos de probabilidad donde el
                            modelo tiene poca data de validación para
                            confiar en su calibración — ver
                            calibracion.factor_confianza(). 1.0 = sin
                            ajuste (comportamiento Kelly cuarto normal).

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

    # Kelly fraccionario — reduce volatilidad. factor_confianza reduce
    # más todavía si esta probabilidad cae en un rango poco validado.
    fraccion_efectiva = fraccion * factor_confianza
    stake_kelly = kelly_completo * fraccion_efectiva

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


def _expandir_over_under(nombre_base: str, prefijo_odds: str,
                          over_under: dict) -> list:
    """De un dict {'over_2_5':0.55,'under_2_5':0.45,...} arma tuplas
    (nombre_mercado, prob, odds_key) para over Y under de cada línea."""
    entradas = []
    lineas_vistas = {k.replace("over_", "").replace("under_", "")
                     for k in over_under if k.startswith(("over_", "under_"))}
    for clave in sorted(lineas_vistas):
        linea_txt = clave.replace("_", ".")
        for lado, etiqueta in (("over", "Over"), ("under", "Under")):
            k = f"{lado}_{clave}"
            if k in over_under:
                entradas.append((
                    f"{nombre_base} {etiqueta} {linea_txt}",
                    over_under[k],
                    f"odds_{prefijo_odds}_{k}",
                    None,  # sin clase de calibración — viene de Poisson, no del clasificador
                ))
    return entradas


def analizar_mercados_kelly(
    prediccion: dict,
    odds: dict,
    bankroll: float = 1000.0,
    fraccion: float = 0.25,
    montecarlo: Optional[dict] = None,
    calibracion: Optional[dict] = None,
) -> list:
    """
    Analiza todos los mercados de un partido y calcula
    el stake óptimo para cada uno usando Kelly.

    Parámetros:
      prediccion  → dict con prob_local, prob_empate, prob_visitante
      odds        → cuotas del bookmaker. 1X2: odds_local/empate/visitante.
                    Resto de mercados (si se pasa montecarlo): claves
                    odds_goles_over_2_5, odds_btts_si, odds_corners_over_9_5,
                    odds_tarjetas_over_2_5, etc. — mercados sin cuota se
                    saltan solos, no hace falta pasarlas todas.
      bankroll    → capital disponible en la moneda que uses
      fraccion    → fracción de Kelly (default 0.25)
      montecarlo  → salida de simular_partido(), para extender el análisis
                    a Over/Under de goles, BTTS, corners y tarjetas además
                    de 1X2. Sin esto, solo analiza 1X2 (comportamiento
                    original).
      calibracion → salida de ajustar_calibracion() (calibracion.py). Si se
                    pasa, la fracción de Kelly de los mercados 1X2 se ajusta
                    por qué tan validada está la calibración en ese rango
                    de probabilidad (ver calcular_kelly factor_confianza).
                    No aplica a O/U ni BTTS ni corners/tarjetas — esos salen
                    de la fórmula de Poisson, no de un clasificador que haga
                    falta calibrar de la misma forma.

    Mercados sin cuota real del bookmaker (ej. goles por equipo — API-Football
    solo cotiza esa línea por mitad de partido, no el partido completo) NO se
    descartan: se devuelven igual con cuota=None/es_value_bet=False/
    sin_cuota=True, para mostrar al menos la probabilidad del modelo en vez
    de desaparecer en silencio (antes se perdían sin aviso).

    Retorna lista de mercados ordenados por EV descendente (los sin cuota
    van al final, ev=0).
    """
    mercados = []
    analisis = construir_lista_mercados(prediccion, montecarlo)

    # Lo aprendido de nuestros propios aciertos y errores por tipo de
    # mercado. Se carga UNA vez acá y no por mercado: son decenas de
    # mercados por partido y el archivo es el mismo para todos.
    from backend.models.calibracion_produccion import cargar as cargar_factores, corregir
    factores_reales = cargar_factores()

    for nombre_mercado, prob, odds_key, clase_calib in analisis:
        if prob <= 0:
            continue
        clave_mercado = odds_key.removeprefix("odds_")
        # Corrige con lo observado en produccion ANTES de calcular EV y
        # stake: si en corners venimos declarando 64% y acertando 10%,
        # apostar sobre el 64% es apostar sobre un numero que ya sabemos
        # que no se cumple.
        prob = corregir(prob, clave_mercado, factores_reales)
        if prob <= 0:
            continue
        cuota = odds.get(odds_key, 0)

        if cuota <= 1.0:
            mercados.append({
                "mercado":        nombre_mercado,
                "clave":          clave_mercado,
                "probabilidad":   round(prob, 4),
                "cuota":          None,
                "ev":             0.0,
                "edge":           0.0,
                "es_value_bet":   False,
                "sin_cuota":      True,
                "stake_pct":      0.0,
                "stake_units":    0.0,
                "cuota_justa":    round(1 / prob, 2),
                "prob_implicita": None,
                "factor_confianza": 1.0,
                "mensaje":        "Sin cuota de bookmaker disponible — probabilidad del modelo",
            })
            continue

        factor = 1.0
        if calibracion is not None and clase_calib is not None:
            factor = factor_confianza(calibracion, clase_calib, prob)

        kelly = calcular_kelly(prob, cuota, fraccion, factor_confianza=factor)

        stake_unidades = kelly["stake_kelly"] * bankroll

        mercados.append({
            "mercado":        nombre_mercado,
            "clave":          clave_mercado,  # para resolver_mercado.py — ver job_cerrar_predicciones.py
            "probabilidad":   round(prob, 4),
            "cuota":          round(cuota, 2),
            "ev":             kelly["ev"],
            "edge":           kelly["edge"],
            "es_value_bet":   kelly["es_value_bet"],
            "sin_cuota":      False,
            "stake_pct":      round(kelly["stake_kelly"] * 100, 2),
            "stake_units":    round(stake_unidades, 2),
            "cuota_justa":    kelly["cuota_justa"],
            "prob_implicita": kelly["prob_implicita"],
            "factor_confianza": round(factor, 3),
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


def construir_lista_mercados(prediccion: dict, montecarlo: Optional[dict] = None) -> list:
    """(nombre, prob, odds_key, clase_calibracion|None) de todos los
    mercados disponibles para un partido — 1X2 siempre, el resto si se
    pasa montecarlo (salida de simular_partido). Extraído de
    analizar_mercados_kelly para que /combinada (parlay.py) pueda buscar
    la probabilidad de CUALQUIER mercado por su odds_key sin duplicar
    esta lista."""
    analisis = [
        ("1X2 Local",     prediccion.get("prob_local",    0), "odds_local",     0),
        ("1X2 Empate",    prediccion.get("prob_empate",   0), "odds_empate",    1),
        ("1X2 Visitante", prediccion.get("prob_visitante",0), "odds_visitante", 2),
    ]

    if montecarlo:
        ou_goles = montecarlo.get("over_under", {})
        analisis += _expandir_over_under("Goles", "goles", ou_goles)

        if "goles_equipo_local" in montecarlo:
            analisis += _expandir_over_under(
                "Goles Local", "goles_equipo_local", montecarlo["goles_equipo_local"])
        if "goles_equipo_visit" in montecarlo:
            analisis += _expandir_over_under(
                "Goles Visitante", "goles_equipo_visit", montecarlo["goles_equipo_visit"])

        if "btts_si" in montecarlo:
            analisis.append(("BTTS Sí", montecarlo["btts_si"], "odds_btts_si", None))
            analisis.append(("BTTS No", montecarlo["btts_no"], "odds_btts_no", None))

        if "corners" in montecarlo:
            analisis += _expandir_over_under(
                "Corners", "corners", montecarlo["corners"].get("over_under", {}))

        if "tarjetas" in montecarlo:
            analisis += _expandir_over_under(
                "Tarjetas", "tarjetas", montecarlo["tarjetas"].get("over_under", {}))

        if "rojas" in montecarlo:
            analisis += _expandir_over_under(
                "Rojas", "rojas", montecarlo["rojas"].get("over_under", {}))

        if "handicap" in montecarlo:
            for clave, datos in montecarlo["handicap"].items():
                linea_txt = f"{datos['linea']:+g}"
                analisis.append((
                    f"Hándicap Local {linea_txt}", datos["gana_local"],
                    f"odds_handicap_local_{clave}", None))
                analisis.append((
                    f"Hándicap Visitante {-datos['linea']:+g}", datos["gana_visitante"],
                    f"odds_handicap_visit_{clave}", None))

        if "primer_tiempo" in montecarlo:
            pt = montecarlo["primer_tiempo"]
            for sufijo, nombre, datos in (
                ("1t", "1er Tiempo", pt["resultado_1t"]),
                ("2t", "2do Tiempo", pt["resultado_2t"]),
            ):
                analisis.append((f"{nombre} Local", datos["prob_local"],
                                  f"odds_{sufijo}_local", None))
                analisis.append((f"{nombre} Empate", datos["prob_empate"],
                                  f"odds_{sufijo}_empate", None))
                analisis.append((f"{nombre} Visitante", datos["prob_visitante"],
                                  f"odds_{sufijo}_visitante", None))
            analisis += _expandir_over_under("Goles 1er Tiempo", "goles_1t", pt["over_under_1t"])

    return analisis


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