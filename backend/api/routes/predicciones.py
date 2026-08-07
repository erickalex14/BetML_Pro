from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.services.prediccion_service import PrediccionService
from backend.models.kelly import analizar_mercados_kelly
from backend.models.calibracion import cargar_calibracion

router = APIRouter()


class SeleccionParlay(BaseModel):
    partido_id: int
    mercado: str  # "local", "empate", "visitante", "goles_over_2_5",
                  # "btts_si", "corners_over_9_5", "tarjetas_over_2_5",
                  # "rojas_over_0_5", "handicap_local_m1_0", "1t_local",
                  # "goles_1t_over_0_5", etc — mismos nombres que las
                  # claves odds_* del endpoint /kelly (sin el prefijo "odds_")
    cuota: Optional[float] = None  # None = usa la mejor cuota real guardada (job_odds.py)


class ParlayRequest(BaseModel):
    selecciones: list[SeleccionParlay]
    bankroll: float = 1000.0
    fraccion: float = 0.25
    guardar: bool = True  # persiste el parlay para MLOps — ver job_cerrar_predicciones.py


def _correr_montecarlo_partido(db: Session, partido, pred: dict,
                                n_simulaciones: int = 10000) -> tuple:
    """Corre Monte Carlo para un partido — xG de Sofascore si está
    disponible (post-partido, útil para backtesting), si no lo estima
    desde las probabilidades del modelo. Corners/tarjetas: promedio de
    los últimos 5 partidos de cada equipo (sin leakage, disponible
    también para partidos futuros). Devuelve (resultado_mc, fuente_xg)."""
    from backend.models.montecarlo import simular_partido
    from backend.features.calculador import calcular_stats_sofascore

    stats = partido.stats_sofascore
    if isinstance(stats, list):
        stats = stats[0] if stats else None

    if stats and stats.xg_local and stats.xg_visitante:
        xg_local, xg_visit = stats.xg_local, stats.xg_visitante
        fuente_xg = "Sofascore"
    else:
        xg_local = max(0.3, pred.get("prob_local", 0.33) * 2.5)
        xg_visit = max(0.3, pred.get("prob_visitante", 0.33) * 2.5)
        fuente_xg = "Estimado desde probabilidades ML"

    sf_local = calcular_stats_sofascore(db, partido.equipo_local_id, partido.fecha, es_local=True)
    sf_visit = calcular_stats_sofascore(db, partido.equipo_visit_id, partido.fecha, es_local=False)

    mc = simular_partido(
        xg_local=xg_local,
        xg_visitante=xg_visit,
        n_simulaciones=n_simulaciones,
        corners_local=sf_local["corners_favor"] or None,
        corners_visit=sf_visit["corners_favor"] or None,
        amarillas_local=sf_local["amarillas_favor"] or None,
        amarillas_visit=sf_visit["amarillas_favor"] or None,
        rojas_local=sf_local["rojas_favor"] or None,
        rojas_visit=sf_visit["rojas_favor"] or None,
        incluir_handicap=True,
        incluir_ht=True,
    )
    return mc, fuente_xg


@router.get("/hoy")
def predicciones_hoy(db: Session = Depends(get_db)):
    service = PrediccionService(db)
    return service.predecir_hoy()


@router.get("/{partido_id}/ensemble")
def prediccion_ensemble(partido_id: int, db: Session = Depends(get_db)):
    """
    Predicción combinada — XGBoost + MLP + LSTM, votación ponderada por
    accuracy de validación de cada modelo. Si MLP o LSTM no están
    entrenados todavía, cae a los modelos que sí estén disponibles.
    """
    from backend.repositories.partido_repo import PartidoRepository
    from backend.models.ensemble import predecir_ensemble

    repo    = PartidoRepository(db)
    partido = repo.get_por_id(partido_id)

    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    pred = predecir_ensemble(db, partido, persistir=True)
    if not pred:
        raise HTTPException(
            status_code=422,
            detail="Sin historial suficiente, o ningún modelo entrenado todavía"
        )

    return pred


@router.get("/{partido_id}/kelly")
def kelly_partido(
    partido_id: int,
    request: Request,
    odds_local:     Optional[float] = None,
    odds_empate:    Optional[float] = None,
    odds_visitante: Optional[float] = None,
    bankroll:       float = 1000.0,
    fraccion:       float = 0.25,
    incluir_mercados_extra: bool = True,
    guardar:        bool = False,
    db: Session = Depends(get_db)
):
    """
    Calcula el stake óptimo con Kelly Criterion para un partido.

    guardar=True persiste cada value bet encontrada como Prediccion,
    para que job_cerrar_predicciones.py (MLOps) las cierre cuando el
    partido termine y /stats/modelo pueda mostrar accuracy real por
    mercado. False por default — consultar Kelly no debería ensuciar el
    tracking cada vez que alguien mira las cuotas.

    Cuotas: si el partido tiene cuotas guardadas por job_odds.py (real,
    de hasta 14 bookmakers vía API-Football gratis), se usan como base
    automáticamente — la mejor cuota disponible por mercado. Cualquier
    odds_* que pases por query param pisa esa cuota automática para ese
    mercado puntual (útil si querés forzar la cuota de UNA casa en
    particular, o si el partido es muy lejano y todavía no tiene cuotas
    guardadas). Mercados: odds_local/empate/visitante, odds_goles_over_2_5,
    odds_btts_si, odds_corners_over_9_5, odds_tarjetas_over_2_5, etc.

    Ejemplo:
      GET /predicciones/123/kelly  (usa cuotas automáticas para todo)
      GET /predicciones/123/kelly?odds_local=2.10  (pisa solo 1X2 Local)
    """
    from backend.repositories.partido_repo import PartidoRepository
    from backend.services.prediccion_service import PrediccionService
    from backend.models.odds_service import obtener_mejores_odds

    repo    = PartidoRepository(db)
    partido = repo.get_por_id(partido_id)

    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    # Genera predicción del modelo ML
    service = PrediccionService(db)
    pred    = service.predecir(partido)

    if not pred:
        raise HTTPException(
            status_code=422,
            detail="Sin historial suficiente para predecir"
        )

    # Base: mejores cuotas guardadas en BD. Encima, lo que venga
    # explícito en la query pisa esa base mercado por mercado.
    odds = obtener_mejores_odds(db, partido_id)
    if odds_local is not None:     odds["odds_local"] = odds_local
    if odds_empate is not None:    odds["odds_empate"] = odds_empate
    if odds_visitante is not None: odds["odds_visitante"] = odds_visitante
    for k, v in request.query_params.items():
        if k.startswith("odds_") and k not in ("odds_local", "odds_empate", "odds_visitante"):
            try:
                odds[k] = float(v)
            except ValueError:
                pass

    montecarlo = None
    if incluir_mercados_extra:
        montecarlo, _ = _correr_montecarlo_partido(db, partido, pred)

    calibracion = cargar_calibracion()

    kelly = analizar_mercados_kelly(
        prediccion=pred,
        odds=odds,
        bankroll=bankroll,
        fraccion=fraccion,
        montecarlo=montecarlo,
        calibracion=calibracion,
    )

    if guardar and kelly["value_bets"]:
        from backend.repositories.prediccion_repo import PrediccionRepository
        repo_pred = PrediccionRepository(db)
        for vb in kelly["value_bets"]:
            repo_pred.crear(
                partido_id=partido_id,
                mercado=vb["clave"],
                prediccion=vb["mercado"],
                probabilidad=vb["probabilidad"],
                confianza=vb["probabilidad"],
            )

    return {
        "partido_id":  partido_id,
        "prediccion":  pred,
        "kelly":       kelly,
        "instrucciones": {
            "value_bets":  kelly["value_bets"],
            "resumen":     f"{kelly['n_value_bets']} apuesta(s) con valor positivo",
        }
    }

@router.get("/{partido_id}/montecarlo")
def montecarlo_partido(
    partido_id:     int,
    n_simulaciones: int = 10000,
    db: Session = Depends(get_db)
):
    """
    Corre simulación Monte Carlo para un partido.
    Usa xG de Sofascore si está disponible,
    si no estima desde las probabilidades del modelo ML.
    """
    from backend.repositories.partido_repo import PartidoRepository
    from backend.services.prediccion_service import PrediccionService

    repo    = PartidoRepository(db)
    partido = repo.get_por_id(partido_id)

    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    service = PrediccionService(db)
    pred    = service.predecir(partido)

    if not pred:
        raise HTTPException(
            status_code=422,
            detail="Sin historial suficiente"
        )

    mc, fuente_xg = _correr_montecarlo_partido(db, partido, pred, n_simulaciones)

    return {
        "partido_id":    partido_id,
        "prediccion_ml": pred,
        "montecarlo":    mc,
        "fuente_xg":     fuente_xg,
        "n_simulaciones":n_simulaciones,
    }


@router.get("/{partido_id}/kelly/portafolio")
def kelly_portafolio_partido(
    partido_id: int,
    request: Request,
    bankroll: float = 1000.0,
    fraccion: float = 0.25,
    n_simulaciones: int = 20000,
    db: Session = Depends(get_db)
):
    """
    Kelly de portafolio — optimiza el stake conjunto de varios mercados
    del MISMO partido a la vez, considerando su correlación real (no los
    trata como apuestas independientes). Acotado a mercados derivados de
    goles (1X2, Over/Under, BTTS) — esos comparten el mismo par
    (goles_local, goles_visit) simulado, así que la correlación entre
    ellos está bien definida. Corners/tarjetas se simulan aparte sin
    correlación con los goles, mezclarlos en el mismo portafolio
    asumiría una independencia que no está modelada — quedan fuera.

    Cuotas: automáticas desde job_odds.py (mejor cuota real guardada por
    mercado) — cualquier odds_* por query param pisa la automática para
    ese mercado puntual. Mercados: odds_local, odds_empate, odds_visitante,
    odds_goles_over_2_5, odds_goles_under_2_5, odds_btts_si, odds_btts_no.

    Ejemplo:
      GET /predicciones/123/kelly/portafolio  (usa cuotas automáticas)
      GET /predicciones/123/kelly/portafolio?odds_local=1.90&bankroll=1000
    """
    from backend.repositories.partido_repo import PartidoRepository
    from backend.services.prediccion_service import PrediccionService
    from backend.models.montecarlo import simular_partido
    from backend.models.kelly_portfolio import kelly_portfolio, probabilidad_ruina
    from backend.models.odds_service import obtener_mejores_odds

    repo    = PartidoRepository(db)
    partido = repo.get_por_id(partido_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    service = PrediccionService(db)
    pred    = service.predecir(partido)
    if not pred:
        raise HTTPException(status_code=422, detail="Sin historial suficiente para predecir")

    odds = obtener_mejores_odds(db, partido_id)
    for k, v in request.query_params.items():
        if k.startswith("odds_"):
            try:
                odds[k] = float(v)
            except ValueError:
                pass

    stats = partido.stats_sofascore
    if isinstance(stats, list):
        stats = stats[0] if stats else None
    if stats and stats.xg_local and stats.xg_visitante:
        xg_local, xg_visit = stats.xg_local, stats.xg_visitante
    else:
        xg_local = max(0.3, pred.get("prob_local", 0.33) * 2.5)
        xg_visit = max(0.3, pred.get("prob_visitante", 0.33) * 2.5)

    mc = simular_partido(xg_local, xg_visit, n_simulaciones=n_simulaciones, devolver_escenarios=True)
    gl, gv = mc["_escenarios"]["goles_local"], mc["_escenarios"]["goles_visit"]
    goles_total = gl + gv

    # (nombre, gana_escenario, odds_key) — solo entra al portafolio si
    # trae cuota en la query
    candidatos = [
        ("1X2 Local", gl > gv, "odds_local"),
        ("1X2 Empate", gl == gv, "odds_empate"),
        ("1X2 Visitante", gl < gv, "odds_visitante"),
        ("Goles Over 2.5", goles_total > 2.5, "odds_goles_over_2_5"),
        ("Goles Under 2.5", goles_total <= 2.5, "odds_goles_under_2_5"),
        ("BTTS Sí", (gl > 0) & (gv > 0), "odds_btts_si"),
        ("BTTS No", ~((gl > 0) & (gv > 0)), "odds_btts_no"),
    ]

    mercados = [
        {"nombre": nombre, "gana_escenario": gana, "cuota": odds[odds_key]}
        for nombre, gana, odds_key in candidatos
        if odds_key in odds and odds[odds_key] > 1.0
    ]

    if not mercados:
        raise HTTPException(
            status_code=422,
            detail="Sin cuotas — pasá al menos odds_local/empate/visitante o odds_goles_*/odds_btts_*"
        )

    portafolio = kelly_portfolio(mercados, fraccion=fraccion)
    riesgo_ruina = probabilidad_ruina(
        mercados, [m["stake_pct"] for m in portafolio["mercados"]],
        bankroll_inicial=bankroll,
    )

    return {
        "partido_id": partido_id,
        "bankroll": bankroll,
        "portafolio": portafolio,
        "stake_total_unidades": round(portafolio["stake_total_pct"] / 100 * bankroll, 2),
        "probabilidad_ruina_temporada": riesgo_ruina,
        "nota_ruina": "P(el bankroll cae bajo 50% en algún punto de 50 fines de semana apostando esta misma combinación)",
    }


@router.post("/combinada")
def apuesta_combinada(body: ParlayRequest, db: Session = Depends(get_db)):
    """
    Apuesta combinada (parlay/acumulada) — varias selecciones de
    partidos DISTINTOS en una sola apuesta, asumiendo independencia
    entre ellos (partidos de equipos y fechas distintas). Para varios
    MERCADOS del MISMO partido (correlacionados entre sí), usar
    /kelly/portafolio en cambio.

    Cualquier mercado de /kelly vale acá (1X2, goles O/U, BTTS, corners,
    tarjetas, rojas, hándicap, 1er/2do tiempo) — mercado usa el mismo
    nombre que la clave odds_* de ese endpoint, sin el prefijo "odds_".
    cuota es opcional por pata — si no se pasa, usa la mejor cuota real
    guardada (job_odds.py); si el partido no tiene cuotas guardadas
    todavía y tampoco se pasó cuota, esa pata da error.

    Body de ejemplo:
      {"selecciones": [
        {"partido_id": 123, "mercado": "local"},
        {"partido_id": 456, "mercado": "goles_over_2_5", "cuota": 1.85}
      ], "bankroll": 1000, "fraccion": 0.25}
    """
    from backend.repositories.partido_repo import PartidoRepository
    from backend.models.parlay import calcular_parlay_kelly
    from backend.models.kelly import construir_lista_mercados
    from backend.models.odds_service import obtener_mejores_odds

    if len(body.selecciones) < 2:
        raise HTTPException(status_code=422, detail="Un parlay necesita 2+ selecciones")

    repo = PartidoRepository(db)
    service = PrediccionService(db)
    selecciones_calc = []

    for sel in body.selecciones:
        partido = repo.get_por_id(sel.partido_id)
        if not partido:
            raise HTTPException(status_code=404, detail=f"Partido {sel.partido_id} no encontrado")

        pred = service.predecir(partido)
        if not pred:
            raise HTTPException(
                status_code=422,
                detail=f"Sin historial suficiente para partido {sel.partido_id}")

        montecarlo, _ = _correr_montecarlo_partido(db, partido, pred)
        mercados_disponibles = construir_lista_mercados(pred, montecarlo)

        odds_key_buscada = f"odds_{sel.mercado}"
        encontrado = next((m for m in mercados_disponibles if m[2] == odds_key_buscada), None)
        if encontrado is None:
            raise HTTPException(
                status_code=422,
                detail=f"mercado inválido para partido {sel.partido_id}: {sel.mercado!r}")

        cuota = sel.cuota
        if cuota is None:
            cuota = obtener_mejores_odds(db, sel.partido_id).get(odds_key_buscada)
        if cuota is None:
            raise HTTPException(
                status_code=422,
                detail=f"partido {sel.partido_id}: sin cuota guardada para {sel.mercado!r} — pasala a mano")

        nombre_mercado, prob, _, _ = encontrado
        selecciones_calc.append({
            "partido_id": sel.partido_id,
            "mercado": nombre_mercado,
            "clave": sel.mercado,
            "prob": prob,
            "cuota": cuota,
        })

    resultado = calcular_parlay_kelly(selecciones_calc, bankroll=body.bankroll, fraccion=body.fraccion)

    if body.guardar and "error" not in resultado:
        from backend.db.modelos import Parlay, ParlaySeleccion
        parlay = Parlay(
            cuota_combinada=resultado["cuota_combinada"],
            prob_combinada=resultado["prob_combinada"],
            stake_pct=resultado["stake_pct"],
            bankroll=body.bankroll,
        )
        db.add(parlay)
        db.flush()  # necesita parlay.id antes de crear las selecciones

        for sc in selecciones_calc:
            db.add(ParlaySeleccion(
                parlay_id=parlay.id,
                partido_id=sc["partido_id"],
                mercado=sc["clave"],
                nombre=sc["mercado"],
                probabilidad=sc["prob"],
                cuota=sc["cuota"],
            ))
        db.commit()
        resultado["parlay_id"] = parlay.id

    return resultado


@router.get("/{partido_id}/jugadores")
def mercados_jugadores(
    partido_id: int,
    n_simulaciones: int = 10000,
    db: Session = Depends(get_db)
):
    """
    Mercados individuales de jugador — tiros, tiros al arco, anotar,
    amarilla, roja. Para el XI probable de cada equipo (no hay
    alineación confirmada hasta ~1h antes del partido; se usa quién jugó
    de titular más seguido en los últimos 5 partidos).
    """
    from backend.repositories.partido_repo import PartidoRepository
    from backend.models.jugadores_montecarlo import simular_jugadores_partido

    repo    = PartidoRepository(db)
    partido = repo.get_por_id(partido_id)

    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    resultado = simular_jugadores_partido(db, partido, n_simulaciones)

    return {
        "partido_id": partido_id,
        "n_simulaciones": n_simulaciones,
        "jugadores": resultado,
    }