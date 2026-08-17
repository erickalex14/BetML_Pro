from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db.modelos import Usuario
from backend.core.deps import get_usuario_actual
from backend.services.prediccion_service import PrediccionService
from backend.models.kelly import analizar_mercados_kelly
from backend.models.calibracion import cargar_calibracion
from backend.core.rate_limit import limiter, usuario_o_ip

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
    selecciones: list[SeleccionParlay] = Field(max_length=12)
    bankroll: float = Field(default=1000.0, gt=0, le=10_000_000)
    fraccion: float = Field(default=0.25, gt=0, le=1)
    guardar: bool = True  # persiste el parlay para MLOps — ver job_cerrar_predicciones.py


def _correr_montecarlo_partido(db: Session, partido, pred: dict,
                                n_simulaciones: int = 10000) -> tuple:
    """Corre Monte Carlo para un partido con datos anteriores al inicio.

    El xG del propio partido nunca entra aquí: después de comenzar sería
    fuga de información y reconstruiría recomendaciones que no existían
    antes del kickoff. Corners/tarjetas: promedio de
    los últimos 5 partidos de cada equipo (sin leakage, disponible
    también para partidos futuros). Devuelve (resultado_mc, fuente_xg)."""
    from backend.models.montecarlo import simular_partido
    from backend.features.calculador import calcular_stats_sofascore

    sf_local = calcular_stats_sofascore(db, partido.equipo_local_id, partido.fecha, es_local=True)
    sf_visit = calcular_stats_sofascore(db, partido.equipo_visit_id, partido.fecha, es_local=False)

    # Encogimiento hacia la media global: el promedio de 5 partidos es
    # muy ruidoso y en rachas extremas mandaba lambdas absurdos (ver
    # backend/features/medias_liga.py — con PSG daba 85% al Over 11.5
    # córners cuando la frecuencia real es 27%).
    from backend.features.medias_liga import medias_globales, encoger, estimar_xg_prepartido
    m = medias_globales(db)
    n_local, n_visit = sf_local["n_con_stats"], sf_visit["n_con_stats"]

    # Nunca derivar goles de P(local)+P(visitante): eso convierte
    # P(empate) en un sesgo mecánico hacia los unders.
    xg_local, xg_visit, fuente_xg = estimar_xg_prepartido(sf_local, sf_visit, m)

    mc = simular_partido(
        xg_local=xg_local,
        xg_visitante=xg_visit,
        n_simulaciones=n_simulaciones,
        corners_local=encoger(sf_local["corners_favor"], n_local, m["corners_local"]),
        corners_visit=encoger(sf_visit["corners_favor"], n_visit, m["corners_visit"]),
        amarillas_local=encoger(sf_local["amarillas_favor"], n_local, m["amarillas_local"]),
        amarillas_visit=encoger(sf_visit["amarillas_favor"], n_visit, m["amarillas_visit"]),
        rojas_local=encoger(sf_local["rojas_favor"], n_local, m["rojas_local"]),
        rojas_visit=encoger(sf_visit["rojas_favor"], n_visit, m["rojas_visit"]),
        incluir_handicap=True,
        incluir_ht=True,
    )
    return mc, fuente_xg


@router.get("/hoy")
def predicciones_hoy(db: Session = Depends(get_db)):
    service = PrediccionService(db)
    return service.predecir_hoy()


@router.get("/mias")
def predicciones_mias(
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
):
    """
    Historial de predicciones guardadas por ESTE usuario (ver POST
    /{id}/guardar-mercados). estado: pendiente|acertada|fallada, sin
    pasar devuelve todo.

    Filtra por usuario: antes devolvía las de todos, así que cualquiera
    veía lo que guardaban los demás. Las generadas por el sistema
    (usuario_id NULL) tampoco aparecen acá — esas viven en la pantalla
    de recomendadas.
    """
    from backend.repositories.prediccion_repo import PrediccionRepository
    from backend.repositories.partido_repo import PartidoRepository

    repo_pred = PrediccionRepository(db)
    repo_partido = PartidoRepository(db)
    filas = repo_pred.listar(estado=estado, usuario_id=usuario.id)

    resultado = []
    for f in filas:
        partido = repo_partido.get_por_id(f.partido_id)
        resultado.append({
            "id": f.id,
            "partido_id": f.partido_id,
            "local": partido.equipo_local.nombre if partido else None,
            "visitante": partido.equipo_visitante.nombre if partido else None,
            # escudos para agrupar por partido en la UI — mismo campo
            # logo_url que ya usa /partidos (ver PartidoService)
            "local_logo": partido.equipo_local.logo_url if partido else None,
            "visitante_logo": partido.equipo_visitante.logo_url if partido else None,
            "liga": partido.liga.nombre if partido else None,
            "estado": partido.estado if partido else None,
            "goles_local": partido.goles_local if partido else None,
            "goles_visit": partido.goles_visitante if partido else None,
            "mercado": f.mercado,
            "prediccion": f.prediccion,
            "probabilidad": f.probabilidad,
            "resultado_real": f.resultado_real,
            "acerto": f.acerto,
            "creado_en": f.creado_en.isoformat() if f.creado_en else None,
        })
    return {"predicciones": resultado, "total": len(resultado)}


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
    mercado puntual (útil para forzar la cuota de UNA casa en
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
    if incluir_mercados_extra and pred.get("origen_prediccion") != "mercado":
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

    if pred.get("origen_prediccion") == "mercado":
        # No se puede descubrir valor comparando una cuota consigo misma.
        for mercado in kelly["todos_mercados"]:
            mercado.update({
                "ev": 0.0, "edge": 0.0, "es_value_bet": False,
                "stake_pct": 0.0, "stake_units": 0.0,
                "mensaje": "Referencia de mercado; falta una señal independiente para Kelly",
            })
        kelly["value_bets"] = []
        kelly["n_value_bets"] = 0

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


class GuardarMercadosRequest(BaseModel):
    claves: list[str] = Field(max_length=50)  # mismas claves de "Todos los mercados"


@router.post("/{partido_id}/guardar-mercados")
def guardar_mercados(
    partido_id: int,
    body: GuardarMercadosRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
):
    """
    Guarda como Prediccion los mercados que el usuario ELIGIÓ (no
    automático como el guardar=True de /kelly, que solo guarda value
    bets) — para que job_cerrar_predicciones.py los cierre contra el
    resultado real cuando el partido termine, y /stats/modelo pueda
    mostrar accuracy real de lo que el usuario efectivamente eligió
    trackear, no solo de las value bets automáticas.

    Body: {"claves": ["local", "goles_over_2_5", "btts_si", ...]} — las
    mismas claves que devuelve /kelly en todos_mercados[].clave.
    """
    from backend.repositories.partido_repo import PartidoRepository
    from backend.repositories.prediccion_repo import PrediccionRepository
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
    montecarlo = None if pred.get("origen_prediccion") == "mercado" else \
        _correr_montecarlo_partido(db, partido, pred)[0]
    todos = analizar_mercados_kelly(prediccion=pred, odds=odds, montecarlo=montecarlo)["todos_mercados"]

    por_clave = {m["clave"]: m for m in todos}
    repo_pred = PrediccionRepository(db)
    guardados = []
    no_encontrados = []
    for clave in body.claves:
        m = por_clave.get(clave)
        if m is None:
            no_encontrados.append(clave)
            continue
        repo_pred.crear(
            partido_id=partido_id,
            mercado=clave,
            prediccion=m["mercado"],
            probabilidad=m["probabilidad"],
            confianza=m["probabilidad"],
            usuario_id=usuario.id,
        )
        guardados.append(clave)

    return {"partido_id": partido_id, "guardados": guardados, "no_encontrados": no_encontrados}


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


@router.get("/{partido_id}/en-vivo")
def prediccion_en_vivo(
    partido_id:     int,
    n_simulaciones: int = 8000,
    db: Session = Depends(get_db)
):
    """
    Probabilidades EN VIVO — recalcula 1X2 y mercados de gol dado el
    marcador y minuto actuales (no un modelo nuevo, Monte Carlo desde
    ahora, ver PrediccionService.predecir_en_vivo). 422 si el partido no
    está en juego, o no tiene minuto (elapsed) todavía.
    """
    from backend.repositories.partido_repo import PartidoRepository
    from backend.services.prediccion_service import PrediccionService

    repo    = PartidoRepository(db)
    partido = repo.get_por_id(partido_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    resultado = PrediccionService(db).predecir_en_vivo(partido, n_simulaciones)
    if resultado is None:
        raise HTTPException(
            status_code=422,
            detail="Partido no está en juego, o falta el minuto todavía, o sin historial suficiente para predecir"
        )
    return resultado


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

    mc_base, _ = _correr_montecarlo_partido(db, partido, pred, n_simulaciones)
    xg_local = mc_base["xg_local"]
    xg_visit = mc_base["xg_visitante"]

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
            detail="Sin cuotas: ingresa al menos odds_local/empate/visitante u odds_goles_*/odds_btts_*"
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
@limiter.limit("10/minute", key_func=usuario_o_ip)
def apuesta_combinada(
    request: Request,
    body: ParlayRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
):
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
    from backend.models.jugadores_montecarlo import (
        mercados_jugadores_calculados, simular_jugadores_partido)

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
        if not pred and not sel.mercado.startswith("jugador_"):
            raise HTTPException(
                status_code=422,
                detail=f"Sin historial suficiente para partido {sel.partido_id}")

        odds_key_buscada = f"odds_{sel.mercado}"
        if sel.mercado.startswith("jugador_"):
            mercados_jugador = mercados_jugadores_calculados(
                simular_jugadores_partido(db, partido, 10000))
            jugador = next((m for m in mercados_jugador if m["clave"] == sel.mercado), None)
            encontrado = ((jugador["mercado"], jugador["probabilidad"], None, None)
                          if jugador else None)
        else:
            montecarlo, _ = _correr_montecarlo_partido(db, partido, pred)
            mercados_disponibles = construir_lista_mercados(pred, montecarlo)
            encontrado = next((m for m in mercados_disponibles if m[2] == odds_key_buscada), None)
        if encontrado is None:
            raise HTTPException(
                status_code=422,
                detail=f"mercado inválido para partido {sel.partido_id}: {sel.mercado!r}")

        cuota = sel.cuota
        if cuota is None and not sel.mercado.startswith("jugador_"):
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
            usuario_id=usuario.id,
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


@router.post("/analizar-captura")
@limiter.limit("10/minute", key_func=usuario_o_ip)
async def analizar_captura(
    request: Request,
    imagen: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
):
    """
    Se carga una captura de pantalla de un parlay/bet builder y el sistema
    lee equipos y mercados (OCR local, gratis, sin API externa — ver
    parser_imagen.py) y devuelve NUESTRA probabilidad para cada
    selección detectada, con recomendación.

    Heurístico, no infalible: capturas limpias de bookmaker andan bien,
    fotos borrosas o layouts raros pueden no reconocer todo — lo que no
    se pudo leer se lista aparte en vez de inventarse.
    """
    import tempfile
    from pathlib import Path
    from backend.models.parser_imagen import analizar_captura_parley, resolver_partido_y_mercados
    from backend.models.kelly import construir_lista_mercados
    from backend.models.odds_service import obtener_mejores_odds
    from backend.services.prediccion_service import PrediccionService

    sufijos = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/webp": ".webp",
    }
    if imagen.content_type not in sufijos:
        raise HTTPException(status_code=415, detail="Formato no permitido: utiliza PNG, JPEG o WEBP")

    total = 0
    excede_tope = False
    with tempfile.NamedTemporaryFile(suffix=sufijos[imagen.content_type], delete=False) as tmp:
        while bloque := await imagen.read(1024 * 1024):
            total += len(bloque)
            if total > 5 * 1024 * 1024:
                excede_tope = True
                break
            tmp.write(bloque)
        ruta_tmp = tmp.name
    if excede_tope:
        Path(ruta_tmp).unlink(missing_ok=True)
        raise HTTPException(status_code=413, detail="La imagen supera 5 MB")

    try:
        analisis = analizar_captura_parley(db, ruta_tmp)
    finally:
        Path(ruta_tmp).unlink(missing_ok=True)

    partido, mercados_detectados, avisos = resolver_partido_y_mercados(db, analisis)

    if partido is None:
        return {
            "reconocido": False,
            "avisos": avisos,
            "lineas_ocr": analisis["lineas_ocr"],
            "sin_reconocer": analisis["sin_reconocer"],
        }

    service = PrediccionService(db)
    pred = service.predecir(partido)
    montecarlo = None
    if pred:
        montecarlo, _ = _correr_montecarlo_partido(db, partido, pred)
    else:
        # sin esto, cada mercado detectado muestra "no se pudo calcular"
        # por separado sin decir por qué — la causa real es una sola
        # (nada de historial para ESTE partido, no un problema por mercado)
        avisos.append(
            f"{partido.equipo_local.nombre} vs {partido.equipo_visitante.nombre} "
            "no tiene historial suficiente para predicción — ningún mercado de "
            "este partido se puede calcular todavía"
        )

    disponibles = construir_lista_mercados(pred, montecarlo) if pred else []
    odds_guardadas = obtener_mejores_odds(db, partido.id)

    resultados = []
    prob_combinada = 1.0
    algun_mercado_calculado = False  # distingue "0 patas calculadas" de "1.0 real" — antes
                                      # devolvía 100% cuando NINGÚN mercado se pudo calcular
    for m in mercados_detectados:
        odds_key = f"odds_{m['mercado']}"
        encontrado = next((e for e in disponibles if e[2] == odds_key), None)
        if encontrado is None:
            resultados.append({**m, "reconocido": False,
                                "aviso": "no se pudo calcular probabilidad para este mercado"})
            continue

        _, prob, _, _ = encontrado
        cuota = odds_guardadas.get(odds_key)
        prob_combinada *= prob
        algun_mercado_calculado = True

        fila = {**m, "reconocido": True, "probabilidad": round(prob, 4)}
        if cuota is not None:
            fila["cuota_disponible"] = cuota
            fila["edge"] = round(prob - (1 / cuota), 4)
            fila["recomendacion"] = "Value bet" if prob > (1 / cuota) else "Sin valor"
        else:
            fila["recomendacion"] = "Probable" if prob > 0.5 else "Improbable"
        resultados.append(fila)

    return {
        "reconocido": True,
        "partido_id": partido.id,
        "avisos": avisos,
        "sin_reconocer": analisis["sin_reconocer"],
        "selecciones": resultados,
        "prob_combinada_estimada": round(prob_combinada, 4) if algun_mercado_calculado else None,
    }


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
    from backend.models.jugadores_montecarlo import mercados_jugadores_calculados

    return {
        "partido_id": partido_id,
        "n_simulaciones": n_simulaciones,
        "jugadores": resultado,
        "mercados": mercados_jugadores_calculados(resultado),
        "nota_cuotas": "Ingresa la cuota de tu casa para calcular EV y Kelly.",
    }


@router.get("/recomendadas")
def predicciones_recomendadas(
    bankroll: float = 1000.0,
    fraccion: float = 0.25,
    n_simulaciones: int = 6000,
    top_individuales: int = 15,
    db: Session = Depends(get_db),
):
    """
    Escanea TODOS los partidos de HOY con predicción + cuotas guardadas
    y arma tres cosas, cada una partida en "fijas" (alta probabilidad,
    para apostar con poco riesgo) y "sonadoras" (cuota alta, probabilidad
    menor y mayor riesgo — todas siguen siendo value bets, con
    edge positivo, no son apuestas al azar):
      1. apuestas_individuales — las mejores value bets por EV, de
         cualquier mercado y cualquier partido (mismo cálculo que /kelly,
         corrido para todos los partidos en vez de uno).
      2. combinadas_mismo_partido — Kelly portafolio (mercados
         correlacionados vía Monte Carlo, ver /kelly/portafolio) de cada
         partido, solo las que dieron stake > 0.
      3. parlays_sugeridos — combinadas entre partidos DISTINTOS, armadas
         con la mejor pata (mayor EV) de cada partido — mismo principio
         de independencia que POST /combinada, acá elegido automático
         en vez de que el usuario seleccione a mano. "fijas" arma con las
         patas de mayor probabilidad, "sonadoras" con las de mayor cuota.

    Vivo, no cacheado — recorre todos los partidos de hoy en cada
    request (unos segundos con ~20-30 partidos). Si se vuelve lento,
    cachear por un rato es la mejora obvia; no se hizo de entrada
    porque no hay todavía evidencia de que haga falta.
    """
    from datetime import timedelta
    from backend.pipeline.config import fecha_hoy_partidos
    from backend.services.cache import guardar_cache, obtener_cache
    hoy = fecha_hoy_partidos()
    usa_cache = (bankroll == 1000.0 and fraccion == 0.25 and
                 n_simulaciones == 6000 and top_individuales == 15)
    clave_cache = f"recomendadas:v2:{hoy}"
    if usa_cache:
        cache = obtener_cache(db, clave_cache)
        if cache is not None:
            return cache

    # Guardia conservadora mientras se acumula un backtest walk-forward.
    # El 55% anterior declaró 71% de media y acertó 20% el fin de semana.
    UMBRAL_FIJA_PROB = 0.65
    from backend.repositories.partido_repo import PartidoRepository
    from backend.models.odds_service import obtener_mejores_odds
    from backend.models.kelly_portfolio import kelly_portfolio
    from backend.models.parlay import calcular_parlay_kelly
    from backend.models.montecarlo import simular_partido
    from backend.pipeline.config import LIGAS_SIN_HISTORIAL_ID
    from backend.db.modelos import Prediccion
    from backend.models.jugadores_montecarlo import (
        mercados_jugadores_calculados, simular_jugadores_partido)

    repo = PartidoRepository(db)
    # amistosos afuera: el modelo predice con la fuerza histórica REAL del
    # equipo, no sabe que en un amistoso suele jugar con suplentes/rotado
    # — un "edge" gigante ahí es más probable que sea el modelo mal
    # calibrado para el contexto que una value bet real (visto en vivo:
    # 60pp de edge en un amistoso, número que no pasa el olfato)
    partidos = [p for p in repo.get_por_fecha(hoy) if p.liga_id not in LIGAS_SIN_HISTORIAL_ID]
    service = PrediccionService(db)
    calibracion = cargar_calibracion()

    individuales = []
    individuales_jugadores = []
    combinadas_partido = []
    mejor_por_partido = []  # una pata por partido, para armar los parlays

    for partido in partidos:
        info_partido = {
            "partido_id": partido.id,
            "local": partido.equipo_local.nombre,
            "visitante": partido.equipo_visitante.nombre,
            "local_logo": partido.equipo_local.logo_url,
            "visitante_logo": partido.equipo_visitante.logo_url,
            "liga": partido.liga.nombre,
            "liga_id": partido.liga_id,
            "hora": partido.fecha.isoformat() if partido.fecha else None,
        }
        cerradas = {
            fila.mercado: fila.acerto
            for fila in db.query(Prediccion)
                          .filter(Prediccion.partido_id == partido.id)
                          .all()
        }
        simulacion_jugadores = simular_jugadores_partido(db, partido, n_simulaciones)
        for mercado_jugador in mercados_jugadores_calculados(simulacion_jugadores):
            individuales_jugadores.append({
                **info_partido,
                **mercado_jugador,
                "acerto": cerradas.get(mercado_jugador["clave"]),
                "estado_partido": partido.estado,
            })

        pred = service.predecir(partido)
        if not pred:
            continue
        if pred.get("origen_prediccion") == "mercado":
            # Las recomendadas requieren una señal independiente de la cuota;
            # una probabilidad derivada de esa misma cuota no demuestra edge.
            continue
        odds = obtener_mejores_odds(db, partido.id)
        if not odds:
            continue

        montecarlo, fuente_xg = _correr_montecarlo_partido(db, partido, pred, n_simulaciones)
        kelly = analizar_mercados_kelly(
            prediccion=pred, odds=odds, bankroll=bankroll, fraccion=fraccion,
            montecarlo=montecarlo, calibracion=calibracion,
        )

        # Estado real de cada mercado si ya se guardó y cerró — es lo que
        # permite tachar en pantalla las que fallaron en vez de mostrar
        # eternamente la recomendación como si siguiera vigente.
        for vb in kelly["value_bets"]:
            individuales.append({
                **info_partido, **vb,
                "acerto": cerradas.get(vb["clave"]),   # None = todavía sin resolver
                "estado_partido": partido.estado,
                "fuente_xg": fuente_xg,
            })

        if kelly["value_bets"]:
            mejor = max(kelly["value_bets"], key=lambda m: m["ev"])
            mejor_por_partido.append({
                **info_partido,
                "mercado_legible": mejor["mercado"],
                "clave": mejor["clave"],
                "prob": mejor["probabilidad"],
                "cuota": mejor["cuota"],
                "apta_fija": (
                    mejor["probabilidad"] >= UMBRAL_FIJA_PROB and
                    (mejor["clave"] in {"local", "empate", "visitante"} or
                     fuente_xg == "Histórico xG prepartido con regresión a la media")
                ),
            })

        # simulación aparte con escenarios crudos — igual que hace
        # /kelly/portafolio (montecarlo de arriba no los trae, se usa
        # para el resto de los mercados vía analizar_mercados_kelly)
        xg_local = montecarlo["xg_local"]
        xg_visit = montecarlo["xg_visitante"]
        mc_escenarios = simular_partido(xg_local, xg_visit, n_simulaciones=n_simulaciones, devolver_escenarios=True)
        gl = mc_escenarios["_escenarios"]["goles_local"]
        gv = mc_escenarios["_escenarios"]["goles_visit"]
        goles_total = gl + gv
        candidatos_portafolio = [
            ("1X2 Local", gl > gv, "odds_local"),
            ("1X2 Empate", gl == gv, "odds_empate"),
            ("1X2 Visitante", gl < gv, "odds_visitante"),
            ("Goles Over 2.5", goles_total > 2.5, "odds_goles_over_2_5"),
            ("Goles Under 2.5", goles_total <= 2.5, "odds_goles_under_2_5"),
            ("BTTS Sí", (gl > 0) & (gv > 0), "odds_btts_si"),
            ("BTTS No", ~((gl > 0) & (gv > 0)), "odds_btts_no"),
        ]
        mercados_portafolio = [
            {"nombre": nombre, "gana_escenario": gana, "cuota": odds[odds_key]}
            for nombre, gana, odds_key in candidatos_portafolio
            if odds_key in odds and odds[odds_key] > 1.0
        ]
        if mercados_portafolio:
            portafolio = kelly_portfolio(mercados_portafolio, fraccion=fraccion)
            if portafolio["stake_total_pct"] > 0:
                combinadas_partido.append({
                    **info_partido,
                    "portafolio": portafolio,
                    "fuente_xg": fuente_xg,
                })

    individuales.sort(key=lambda m: m["ev"], reverse=True)
    def _apta_fija_individual(m: dict) -> bool:
        if m["probabilidad"] < UMBRAL_FIJA_PROB:
            return False
        if m["clave"] in {"local", "empate", "visitante"}:
            return m.get("factor_confianza", 0) >= 0.75
        return m.get("fuente_xg") == "Histórico xG prepartido con regresión a la media"

    individuales_fijas = [m for m in individuales if _apta_fija_individual(m)][:top_individuales]
    individuales_sonadoras = [m for m in individuales if not _apta_fija_individual(m)][:top_individuales]
    individuales_jugadores.sort(key=lambda m: m["probabilidad"], reverse=True)
    jugadores_fijas = [
        m for m in individuales_jugadores
        if m["probabilidad"] >= 0.65 and m.get("n_partidos_historial", 0) >= 5
    ][:top_individuales]
    jugadores_sonadoras = [
        m for m in individuales_jugadores
        if m not in jugadores_fijas and m["probabilidad"] >= 0.30
    ][:top_individuales]

    combinadas_partido.sort(key=lambda c: c["portafolio"]["ev_portafolio"], reverse=True)

    def _prob_promedio_portafolio(c: dict) -> float:
        mercados = c["portafolio"]["mercados"]
        return sum(m["probabilidad"] for m in mercados) / len(mercados) if mercados else 0.0

    combinadas_fijas = [
        c for c in combinadas_partido
        if (_prob_promedio_portafolio(c) >= UMBRAL_FIJA_PROB and
            c.get("fuente_xg") == "Histórico xG prepartido con regresión a la media")
    ][:5]
    combinadas_sonadoras = [c for c in combinadas_partido if c not in combinadas_fijas][:5]

    def _armar_parlays(candidatos: list) -> list:
        parlays = []
        for n in (2, 3, 4):
            if len(candidatos) < n:
                continue
            elegidos = candidatos[:n]
            resultado = calcular_parlay_kelly(
                [{"partido_id": s["partido_id"], "mercado": s["clave"],
                  "prob": s["prob"], "cuota": s["cuota"]} for s in elegidos],
                bankroll=bankroll, fraccion=fraccion,
            )
            # resultado ya trae su propia "selecciones" (solo prob, sin
            # nombres) — se descarta a favor de la versión con nombres
            # de equipo de acá, si no el **resultado de abajo la pisa
            resultado.pop("selecciones", None)
            parlays.append({
                "n_patas": n,
                "selecciones": [
                    {"partido_id": s["partido_id"], "local": s["local"], "visitante": s["visitante"],
                     "mercado": s["mercado_legible"]}
                    for s in elegidos
                ],
                **resultado,
            })
        return parlays

    parlays_fijas, parlays_sonadoras = [], []
    if len(mejor_por_partido) >= 2:
        # Fijas: arma con las patas de MAYOR probabilidad (mismo criterio
        # de antes). Soñadoras: con las de MAYOR cuota — combos de
        # underdogs con edge positivo, cuota combinada mucho más jugosa.
        candidatos_fijas = [m for m in mejor_por_partido if m["apta_fija"]]
        parlays_fijas = _armar_parlays(sorted(candidatos_fijas, key=lambda m: m["prob"], reverse=True))
        parlays_sonadoras = _armar_parlays(sorted(mejor_por_partido, key=lambda m: m["cuota"], reverse=True))

    respuesta = {
        "fecha": str(hoy),
        "apuestas_individuales": {"fijas": individuales_fijas, "sonadoras": individuales_sonadoras},
        "mercados_jugadores": {"fijas": jugadores_fijas, "sonadoras": jugadores_sonadoras},
        "combinadas_mismo_partido": {"fijas": combinadas_fijas, "sonadoras": combinadas_sonadoras},
        "parlays_sugeridos": {"fijas": parlays_fijas, "sonadoras": parlays_sonadoras},
    }
    if usa_cache:
        guardar_cache(db, clave_cache, respuesta, timedelta(minutes=30))
    return respuesta
