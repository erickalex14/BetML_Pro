import logging
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
from scipy.stats import poisson

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent.parent.parent
RHO_PATH = ROOT_DIR / "data" / "models" / "rho_dixon_coles.pkl"

# Correlación Dixon-Coles para marcadores bajos (0-0, 1-0, 0-1, 1-1).
# Poisson independiente asume que los goles de local y visitante no se
# afectan entre sí — en la realidad los marcadores bajos están
# correlacionados (ej: 0-0 y 1-1 ocurren más de lo que Poisson puro
# predice, porque ambos equipos juegan más cauteloso con el marcador
# cerca). rho negativo es el signo estándar en la literatura (Dixon &
# Coles 1997, rho ≈ -0.13 para fútbol inglés).
# Default de literatura si todavía no se ajustó con datos propios —
# ver ajustar_rho_dixon_coles() para el fit por MLE sobre partidos reales.
RHO_DIXON_COLES_DEFAULT = -0.13

MAX_GOLES_GRID = 10  # cola de Poisson(λ<4) es despreciable pasado esto

# Fracción de goles que ocurre en el primer tiempo — medida sobre ~16k
# partidos reales en BD (20148 de 45843 goles), no un supuesto 50/50.
# Se usa para repartir cada gol simulado del partido completo entre 1T/2T
# (binomial por gol), no para simular dos medios partidos independientes.
FRACCION_GOLES_HT = 0.4395

LINEAS_HANDICAP = [-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0]


def estimar_fraccion_restante(estado: str, minuto: Optional[int]) -> Optional[float]:
    """Fracción del partido que falta jugar (0-1), para escalar el xG
    pre-partido en la predicción en vivo (ver predecir_en_vivo() en
    prediccion_service.py). Modelo lineal simple — asume ritmo de gol
    constante por minuto, no hay curva real ajustada a datos propios
    todavía (ponytail: upgrade si hace falta más precisión en el 2do
    tiempo, donde el ritmo real es más alto).

    None si el estado no es simulable así: 'ET'/'P' (tiempo extra/penales,
    otra dinámica de gol), o no está en juego, o falta el minuto (elapsed
    de API-Football, se guarda apenas arranca — si falta es que la última
    actualización llegó justo antes del pitido inicial)."""
    if estado == "HT":
        return 0.5
    if estado not in ("1H", "2H") or minuto is None:
        return None
    return max(0.0, min(1.0, (90 - minuto) / 90))


def cargar_rho() -> float:
    """rho ajustado a datos propios si ya se corrió
    ajustar_rho_dixon_coles(), si no el valor de literatura."""
    if RHO_PATH.exists():
        return joblib.load(RHO_PATH)
    return RHO_DIXON_COLES_DEFAULT


def _tau_dixon_coles(x: int, y: int, lam: float, mu: float, rho: float) -> float:
    """Factor de corrección de Dixon-Coles para el marcador (x,y)."""
    if x == 0 and y == 0:
        return 1 - (lam * mu * rho)
    if x == 0 and y == 1:
        return 1 + (lam * rho)
    if x == 1 and y == 0:
        return 1 + (mu * rho)
    if x == 1 and y == 1:
        return 1 - rho
    return 1.0


def _grid_marcadores(lam: float, mu: float, rho: float,
                      max_goles: int = MAX_GOLES_GRID) -> np.ndarray:
    """Grilla (max_goles+1)x(max_goles+1) de P(goles_local=x, goles_visit=y)
    con la corrección Dixon-Coles aplicada, normalizada a sumar 1."""
    goles = np.arange(max_goles + 1)
    p_local = poisson.pmf(goles, max(lam, 0.01))
    p_visit = poisson.pmf(goles, max(mu, 0.01))
    grid = np.outer(p_local, p_visit)

    for x in (0, 1):
        for y in (0, 1):
            grid[x, y] *= _tau_dixon_coles(x, y, lam, mu, rho)

    grid = np.clip(grid, 0, None)  # rho grande podría dar negativos
    return grid / grid.sum()


def simular_partido(
        xg_local: float,
        xg_visitante: float,
        n_simulaciones: int = 10000,
        seed: Optional[int] = 42,
        rho: Optional[float] = None,
        corners_local: Optional[float] = None,
        corners_visit: Optional[float] = None,
        amarillas_local: Optional[float] = None,
        amarillas_visit: Optional[float] = None,
        rojas_local: Optional[float] = None,
        rojas_visit: Optional[float] = None,
        incluir_handicap: bool = False,
        incluir_ht: bool = False,
        devolver_escenarios: bool = False,
        goles_local_base: int = 0,
        goles_visit_base: int = 0,
) -> dict:
    """
    Simula un partido N veces muestreando de la distribución conjunta
    Poisson bivariada con corrección Dixon-Coles.

    A diferencia de dos np.random.poisson independientes, esto sí captura
    la correlación real entre los goles de ambos equipos en marcadores
    bajos — un 0-0 no es simplemente "P(local=0) × P(visit=0)".

    Parámetros:
      xg_local, xg_visitante → Expected Goals de cada equipo
      n_simulaciones          → tamaño de la muestra Monte Carlo
      seed                    → semilla para reproducibilidad
      rho                     → correlación Dixon-Coles. None (default)
                                usa cargar_rho() — el valor ajustado a
                                datos propios si existe, si no literatura.
      corners_local/visit     → si se pasan, simula mercado de corners (Poisson
                                independiente — sin corrección de correlación,
                                no hay evidencia de que aplique igual que a goles)
      amarillas_local/visit   → si se pasan, simula mercado de tarjetas amarillas (ídem)
      rojas_local/visit       → si se pasan, simula mercado de tarjetas rojas (ídem)
      incluir_handicap        → agrega hándicap asiático, derivado de la
                                diferencia de goles ya simulada (no cuesta
                                muestras extra, es la misma simulación vista
                                distinto)
      incluir_ht              → agrega resultado 1er/2do tiempo y over/under
                                de goles en el 1er tiempo. Reparte cada gol
                                simulado del partido completo entre 1T/2T con
                                FRACCION_GOLES_HT (medida en datos reales) —
                                no es una simulación independiente del 1er
                                tiempo, es un split del resultado ya simulado.
      goles_local_base/visit_base → goles YA anotados (partido en vivo) que
                                se suman a cada simulación antes de calcular
                                1X2/over-under/marcadores/hándicap — xg_local/
                                xg_visitante deben ser el xG RESTANTE (no el
                                del partido completo) para que esto represente
                                "cómo termina desde acá". Ver
                                predecir_en_vivo() en prediccion_service.py.
      devolver_escenarios      → incluye resultado["_escenarios"] con los
                                arrays crudos (goles_local, goles_visit, y
                                corners/tarjetas si se pidieron) — un valor
                                por simulación, en el MISMO orden en las
                                distintas variables. Kelly de portafolio lo
                                necesita para capturar la correlación real
                                entre mercados del mismo partido (ver
                                kelly_portfolio.py): no sirve promediar cada
                                mercado por separado, hace falta saber qué
                                pasó en cada simulación a la vez.

    Retorna: probabilidades 1X2, top marcadores, over/under, BTTS,
    incertidumbre, percentiles, y el resto de mercados si se pidieron.
    """
    if seed is not None:
        np.random.seed(seed)

    if rho is None:
        rho = cargar_rho()

    lam = max(xg_local, 0.1)
    mu = max(xg_visitante, 0.1)

    grid = _grid_marcadores(lam, mu, rho)
    max_goles = grid.shape[0] - 1

    # Muestrea pares (goles_local, goles_visit) de la grilla conjunta —
    # el equivalente Monte Carlo de "tirar" el marcador exacto según su
    # probabilidad real, corrección Dixon-Coles incluida.
    idx_planos = np.random.choice(
        grid.size, size=n_simulaciones, p=grid.ravel()
    )
    goles_local = idx_planos // (max_goles + 1) + goles_local_base
    goles_visit = idx_planos % (max_goles + 1) + goles_visit_base

    # ── RESULTADOS 1X2 ─────────────────────────────────────
    victorias_local = int(np.sum(goles_local > goles_visit))
    empates = int(np.sum(goles_local == goles_visit))
    victorias_visit = int(np.sum(goles_local < goles_visit))

    prob_local = round(victorias_local / n_simulaciones, 4)
    prob_empate = round(empates / n_simulaciones, 4)
    prob_visit = round(victorias_visit / n_simulaciones, 4)

    # ── Distribución de marcadores ─────────────────────────
    marcadores = {}
    goles_totales = goles_local + goles_visit

    for i in range(n_simulaciones):
        gl = int(goles_local[i])
        gv = int(goles_visit[i])
        marcador = f"{gl}-{gv}"
        marcadores[marcador] = marcadores.get(marcador, 0) + 1

    top_marcadores = sorted(
        [
            {
                "marcador": k,
                "probabilidad": round(v / n_simulaciones, 4),
                "porcentaje": round(v / n_simulaciones * 100, 1),
                "goles_local": int(k.split("-")[0]),
                "goles_visit": int(k.split("-")[1]),
            }
            for k, v in marcadores.items()
        ],
        key=lambda x: x["probabilidad"],
        reverse=True,
    )[:10]

    # Over / under
    over_under = {}
    for linea in [0.5, 1.5, 2.5, 3.5, 4.5]:
        over = int(np.sum(goles_totales > linea))
        under = int(np.sum(goles_totales <= linea))
        over_under[f"over_{str(linea).replace('.', '_')}"] = round(
            over / n_simulaciones, 4)
        over_under[f"under_{str(linea).replace('.', '_')}"] = round(
            under / n_simulaciones, 4)

    # Over/under de goles POR EQUIPO — mismas muestras ya tiradas, sin
    # gasto extra (a diferencia de corners/tarjetas no hace falta un
    # Poisson aparte, goles_local/goles_visit ya están).
    goles_equipo_local = {}
    goles_equipo_visit = {}
    for linea in [0.5, 1.5, 2.5]:
        clave = str(linea).replace(".", "_")
        goles_equipo_local[f"over_{clave}"] = round(float(np.mean(goles_local > linea)), 4)
        goles_equipo_local[f"under_{clave}"] = round(float(np.mean(goles_local <= linea)), 4)
        goles_equipo_visit[f"over_{clave}"] = round(float(np.mean(goles_visit > linea)), 4)
        goles_equipo_visit[f"under_{clave}"] = round(float(np.mean(goles_visit <= linea)), 4)

    # BTTS
    btts_si = int(np.sum((goles_local > 0) & (goles_visit > 0)))
    btts_no = n_simulaciones - btts_si

    prom_goles_local = round(float(np.mean(goles_local)), 2)
    prom_goles_visit = round(float(np.mean(goles_visit)), 2)
    prom_goles_total = round(float(np.mean(goles_totales)), 2)

    max_prob = max(prob_local, prob_empate, prob_visit)
    incertidumbre = round(1 - max_prob, 4)

    percentiles = {
        "p10": int(np.percentile(goles_totales, 10)),
        "p25": int(np.percentile(goles_totales, 25)),
        "p50": int(np.percentile(goles_totales, 50)),
        "p75": int(np.percentile(goles_totales, 75)),
        "p90": int(np.percentile(goles_totales, 90)),
    }

    resultado = {
        "n_simulaciones": n_simulaciones,
        "xg_local": xg_local,
        "xg_visitante": xg_visitante,
        "rho_dixon_coles": rho,

        "prob_local": prob_local,
        "prob_empate": prob_empate,
        "prob_visitante": prob_visit,

        "top_marcadores": top_marcadores,
        "over_under": over_under,
        "goles_equipo_local": goles_equipo_local,
        "goles_equipo_visit": goles_equipo_visit,

        "btts_si": round(btts_si / n_simulaciones, 4),
        "btts_no": round(btts_no / n_simulaciones, 4),

        "prom_goles_local": prom_goles_local,
        "prom_goles_visit": prom_goles_visit,
        "prom_goles_total": prom_goles_total,

        "incertidumbre": incertidumbre,
        "percentiles_goles_totales": percentiles,
    }

    _escenarios = {"goles_local": goles_local, "goles_visit": goles_visit} if devolver_escenarios else None

    if corners_local is not None and corners_visit is not None:
        resultado["corners"] = _simular_mercado_conteo(
            corners_local, corners_visit, n_simulaciones,
            lineas=[7.5, 8.5, 9.5, 10.5, 11.5],
            escenarios_out=_escenarios, prefijo="corners")

    if amarillas_local is not None and amarillas_visit is not None:
        resultado["tarjetas"] = _simular_mercado_conteo(
            amarillas_local, amarillas_visit, n_simulaciones,
            lineas=[1.5, 2.5, 3.5, 4.5],
            escenarios_out=_escenarios, prefijo="tarjetas")

    if rojas_local is not None and rojas_visit is not None:
        resultado["rojas"] = _simular_mercado_conteo(
            rojas_local, rojas_visit, n_simulaciones,
            lineas=[0.5, 1.5],
            escenarios_out=_escenarios, prefijo="rojas")

    if incluir_handicap:
        resultado["handicap"] = _handicap_asiatico(goles_local, goles_visit)

    if incluir_ht:
        resultado["primer_tiempo"] = _simular_medio_tiempo(goles_local, goles_visit, n_simulaciones)

    if devolver_escenarios:
        resultado["_escenarios"] = _escenarios

    return resultado


def _handicap_asiatico(goles_local: np.ndarray, goles_visit: np.ndarray) -> dict:
    """Hándicap asiático derivado de la diferencia de goles ya simulada
    (no consume muestras nuevas). Línea aplicada al LOCAL: en +1.5 el
    local cubre si pierde por 0 o gana; en -1.5 necesita ganar por 2+.
    Líneas enteras (0, ±1, ±2) permiten push (empate del hándicap, se
    devuelve la apuesta) — las .5 nunca empatan."""
    diferencia = goles_local - goles_visit
    lineas = {}
    for linea in LINEAS_HANDICAP:
        ajustada = diferencia + linea
        clave = str(linea).replace(".", "_").replace("-", "m")
        lineas[clave] = {
            "linea": linea,
            "gana_local": round(float(np.mean(ajustada > 0)), 4),
            "push": round(float(np.mean(ajustada == 0)), 4),
            "gana_visitante": round(float(np.mean(ajustada < 0)), 4),
        }
    return lineas


def _simular_medio_tiempo(goles_local: np.ndarray, goles_visit: np.ndarray,
                           n_simulaciones: int) -> dict:
    """Reparte los goles YA simulados del partido completo entre 1T/2T —
    cada gol, independientemente, ocurrió en el primer tiempo con
    probabilidad FRACCION_GOLES_HT (medida en datos reales, ver arriba).
    No es un segundo modelo de Poisson para el medio tiempo: es un split
    binomial del resultado que ya se tiró."""
    gl_ht = np.random.binomial(goles_local, FRACCION_GOLES_HT)
    gv_ht = np.random.binomial(goles_visit, FRACCION_GOLES_HT)
    gl_2t = goles_local - gl_ht
    gv_2t = goles_visit - gv_ht

    def resultado_1x2(gl, gv):
        return {
            "prob_local": round(float(np.mean(gl > gv)), 4),
            "prob_empate": round(float(np.mean(gl == gv)), 4),
            "prob_visitante": round(float(np.mean(gl < gv)), 4),
        }

    total_ht = gl_ht + gv_ht
    over_under_ht = {}
    for linea in [0.5, 1.5, 2.5]:
        clave = str(linea).replace(".", "_")
        over_under_ht[f"over_{clave}"] = round(float(np.mean(total_ht > linea)), 4)
        over_under_ht[f"under_{clave}"] = round(float(np.mean(total_ht <= linea)), 4)

    return {
        "resultado_1t": resultado_1x2(gl_ht, gv_ht),
        "resultado_2t": resultado_1x2(gl_2t, gv_2t),
        "over_under_1t": over_under_ht,
        "prom_goles_1t": round(float(np.mean(total_ht)), 2),
    }


def _simular_mercado_conteo(lam_local: float, lam_visit: float,
                             n_simulaciones: int, lineas: list,
                             escenarios_out: Optional[dict] = None,
                             prefijo: str = "") -> dict:
    """Mercado over/under genérico vía Poisson independiente (corners,
    tarjetas) — sin corrección de correlación tipo Dixon-Coles: esa
    corrección es específica del comportamiento de marcadores de fútbol,
    no hay evidencia publicada de que aplique igual a corners/tarjetas.

    escenarios_out: si se pasa un dict, le agrega los arrays crudos
    (local/visit/total, uno por simulación) bajo f"{prefijo}_local" etc —
    usado por Kelly de portafolio para ver la correlación real entre
    mercados del mismo partido."""
    local = np.random.poisson(lam=max(lam_local, 0.01), size=n_simulaciones)
    visit = np.random.poisson(lam=max(lam_visit, 0.01), size=n_simulaciones)
    total = local + visit

    if escenarios_out is not None:
        escenarios_out[f"{prefijo}_local"] = local
        escenarios_out[f"{prefijo}_visit"] = visit
        escenarios_out[f"{prefijo}_total"] = total

    over_under = {}
    for linea in lineas:
        clave = str(linea).replace(".", "_")
        over_under[f"over_{clave}"] = round(float(np.mean(total > linea)), 4)
        over_under[f"under_{clave}"] = round(float(np.mean(total <= linea)), 4)

    return {
        "promedio_local": round(float(np.mean(local)), 2),
        "promedio_visit": round(float(np.mean(visit)), 2),
        "promedio_total": round(float(np.mean(total)), 2),
        "over_under": over_under,
    }


def simular_con_prediccion(prediccion: dict,
                            n_simulaciones: int = 10000) -> dict:
    """
    Corre Monte Carlo usando las probabilidades del modelo ML
    cuando no hay xG disponible.

    Estima el xG a partir de las probabilidades:
    - Equipo favorito → xG más alto
    - Equipo underdog → xG más bajo
    """
    prob_l = prediccion.get("prob_local", 0.33)
    prob_v = prediccion.get("prob_visitante", 0.33)

    xg_local = max(0.3, prob_l * 2.5)
    xg_visit = max(0.3, prob_v * 2.5)

    return simular_partido(xg_local, xg_visit, n_simulaciones)


def ajustar_rho_dixon_coles(db, guardar: bool = True) -> float:
    """MLE de rho sobre partidos reales con xG de Sofascore.

    A diferencia del Dixon-Coles original (que fija rho junto con
    parámetros de ataque/defensa por equipo, ajustados todos a la vez),
    acá se usa el xG YA disponible como λ/μ de cada partido y se busca el
    único rho que mejor explica el marcador real observado dado ese xG.
    Es un fit más chico y directo — no reconstruye un sistema de rating
    de equipos que XGBoost/MLP/LSTM ya cubren por su cuenta.
    """
    from scipy.optimize import minimize_scalar
    from sqlalchemy import text

    filas = db.execute(text("""
        select e.xg_local, e.xg_visitante, p.goles_local, p.goles_visitante
        from partidos p join estadisticas_sofascores e on e.partido_id = p.id
        where e.xg_local is not null and e.xg_visitante is not null
          and p.goles_local is not null and p.goles_visitante is not null
          and e.xg_local > 0 and e.xg_visitante > 0
    """)).fetchall()

    if len(filas) < 500:
        log.warning(f"Solo {len(filas)} partidos con xG real — muy pocos para un MLE confiable")
        return RHO_DIXON_COLES_DEFAULT

    lams = np.array([f[0] for f in filas])
    mus = np.array([f[1] for f in filas])
    xs = np.array([int(f[2]) for f in filas])  # goles reales, sin clampear —
    ys = np.array([int(f[3]) for f in filas])  # _tau_dixon_coles ya sabe que
                                                # solo (0,0)/(0,1)/(1,0)/(1,1)
                                                # llevan corrección, el resto es 1.0

    def neg_log_likelihood(rho):
        taus = np.array([_tau_dixon_coles(x, y, lam, mu, rho)
                          for x, y, lam, mu in zip(xs, ys, lams, mus)])
        p_indep = poisson.pmf(xs, lams) * poisson.pmf(ys, mus)
        p = np.clip(taus * p_indep, 1e-10, None)
        return -np.sum(np.log(p))

    resultado = minimize_scalar(neg_log_likelihood, bounds=(-0.3, 0.3), method="bounded")
    rho_ajustado = float(resultado.x)

    log.info(f"rho Dixon-Coles ajustado: {rho_ajustado:.4f} "
             f"(literatura: {RHO_DIXON_COLES_DEFAULT}, n={len(filas)} partidos)")

    if guardar:
        RHO_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(rho_ajustado, RHO_PATH)
        log.info(f"rho guardado: {RHO_PATH}")

    return rho_ajustado


if __name__ == "__main__":
    from backend.db.database import SessionLocal
    db = SessionLocal()
    ajustar_rho_dixon_coles(db)
    db.close()
