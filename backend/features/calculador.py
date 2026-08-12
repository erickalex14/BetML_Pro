import logging
from typing import Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session
from backend.db.modelos import Partido, EstadisticaSofascore, EstadisticaJugador
from backend.pipeline.config import LIGAS_SIN_HISTORIAL_ID

log = logging.getLogger(__name__)

N_DIMS_SECUENCIA = 7  # [gf, gc, resultado, xg_favor, xg_contra, posesion, es_local]


def obtener_secuencia_equipo(db: Session, equipo_id: int, fecha_limite,
                              n: int = 10) -> list:
    """Últimos n partidos del equipo (local o visitante, cualquiera de
    los dos) antes de fecha_limite, en orden CRONOLÓGICO ascendente —
    para alimentar un LSTM. Cada paso temporal es un vector:
    [goles_favor, goles_contra, resultado(-1/0/1), xg_favor, xg_contra,
    posesion, es_local(0/1)].

    A diferencia de calcular_forma (que agrega los últimos N partidos en
    un promedio), esto preserva el orden y cada partido individual — el
    LSTM necesita la secuencia cruda para distinguir "perdió los últimos
    3 seguidos" de "perdió 3 de los últimos 10 salteados".
    """
    partidos = (
        db.query(Partido)
        .filter(
            or_(Partido.equipo_local_id == equipo_id,
                Partido.equipo_visit_id == equipo_id),
            Partido.fecha < fecha_limite,
            Partido.estado == "FT",
            Partido.liga_id.notin_(LIGAS_SIN_HISTORIAL_ID),
        )
        .order_by(Partido.fecha.desc())
        .limit(n)
        .all()
    )
    partidos = list(reversed(partidos))  # cronológico ascendente

    secuencia = []
    for p in partidos:
        es_local = (p.equipo_local_id == equipo_id)
        gf = (p.goles_local if es_local else p.goles_visitante) or 0
        gc = (p.goles_visitante if es_local else p.goles_local) or 0
        resultado = 1 if gf > gc else (-1 if gf < gc else 0)

        stats = p.stats_sofascore
        if isinstance(stats, list):
            stats = stats[0] if stats else None

        xg_favor = xg_contra = 0.0
        posesion = 50.0
        if stats:
            xg_favor = (stats.xg_local if es_local else stats.xg_visitante) or 0.0
            xg_contra = (stats.xg_visitante if es_local else stats.xg_local) or 0.0
            posesion = (stats.posesion_local if es_local else stats.posesion_visitante) or 50.0

        secuencia.append([
            float(gf), float(gc), float(resultado),
            xg_favor, xg_contra, posesion, 1.0 if es_local else 0.0,
        ])

    return secuencia


def calcular_forma(db: Session, equipo_id: int, fecha_limite,
                   es_local: bool, n: int = 5) -> dict:
    """
    Forma reciente del equipo en los últimos N partidos
    jugando en casa (es_local=True) o fuera (es_local=False).
    """
    if es_local:
        partidos = (
            db.query(Partido)
            .filter(
                Partido.equipo_local_id == equipo_id,
                Partido.fecha < fecha_limite,
                Partido.estado == "FT",
                Partido.goles_local != None,
                Partido.liga_id.notin_(LIGAS_SIN_HISTORIAL_ID),
            )
            .order_by(Partido.fecha.desc())
            .limit(n).all()
        )
    else:
        partidos = (
            db.query(Partido)
            .filter(
                Partido.equipo_visit_id == equipo_id,
                Partido.fecha < fecha_limite,
                Partido.estado == "FT",
                Partido.goles_visitante != None,
                Partido.liga_id.notin_(LIGAS_SIN_HISTORIAL_ID),
            )
            .order_by(Partido.fecha.desc())
            .limit(n).all()
        )

    if not partidos:
        return {
            "puntos": 0, "goles_favor": 0.0,
            "goles_contra": 0.0, "n_partidos": 0
        }

    puntos = 0
    goles_favor  = []
    goles_contra = []

    for p in partidos:
        if es_local:
            gf = p.goles_local     or 0
            gc = p.goles_visitante or 0
        else:
            gf = p.goles_visitante or 0
            gc = p.goles_local     or 0

        if gf > gc:    puntos += 3
        elif gf == gc: puntos += 1

        goles_favor.append(gf)
        goles_contra.append(gc)

    return {
        "puntos":       puntos,
        "goles_favor":  round(sum(goles_favor)  / len(goles_favor),  2),
        "goles_contra": round(sum(goles_contra) / len(goles_contra), 2),
        "n_partidos":   len(partidos)
    }


def calcular_stats_sofascore(db: Session, equipo_id: int,
                              fecha_limite, es_local: bool,
                              n: int = 5) -> dict:
    """
    Promedio de stats avanzadas de Sofascore de los
    últimos N partidos — xG, tiros, corners, presiones,
    duelos. Estas son las features diferenciales del modelo.
    """
    if es_local:
        partidos = (
            db.query(Partido)
            .filter(
                Partido.equipo_local_id == equipo_id,
                Partido.fecha < fecha_limite,
                Partido.estado == "FT",
                Partido.liga_id.notin_(LIGAS_SIN_HISTORIAL_ID),
            )
            .order_by(Partido.fecha.desc())
            .limit(n).all()
        )
    else:
        partidos = (
            db.query(Partido)
            .filter(
                Partido.equipo_visit_id == equipo_id,
                Partido.fecha < fecha_limite,
                Partido.estado == "FT",
                Partido.liga_id.notin_(LIGAS_SIN_HISTORIAL_ID),
            )
            .order_by(Partido.fecha.desc())
            .limit(n).all()
        )

    vacio = {
        "xg_favor": 0.0, "xg_contra": 0.0,
        "tiros_favor": 0.0, "tiros_contra": 0.0,
        "tiros_arco_favor": 0.0, "tiros_arco_contra": 0.0,
        "corners_favor": 0.0, "corners_contra": 0.0,
        "presiones_favor": 0.0, "presiones_contra": 0.0,
        "posesion": 0.0, "amarillas_favor": 0.0, "rojas_favor": 0.0, "n_con_stats": 0
    }

    if not partidos:
        return vacio

    stats_acum = {k: [] for k in vacio if k != "n_con_stats"}
    n_con_stats = 0

    for p in partidos:
        s = p.stats_sofascore
        if isinstance(s, list):
            s = s[0] if s else None
        if not s:
            continue
        if not s:
            continue

        n_con_stats += 1

        if es_local:
            stats_acum["xg_favor"].append(s.xg_local or 0)
            stats_acum["xg_contra"].append(s.xg_visitante or 0)
            stats_acum["tiros_favor"].append(s.tiros_local or 0)
            stats_acum["tiros_contra"].append(s.tiros_visitante or 0)
            stats_acum["tiros_arco_favor"].append(s.tiros_arco_local or 0)
            stats_acum["tiros_arco_contra"].append(s.tiros_arco_visitante or 0)
            stats_acum["corners_favor"].append(s.corners_local or 0)
            stats_acum["corners_contra"].append(s.corners_visitante or 0)
            stats_acum["presiones_favor"].append(s.presiones_local or 0)
            stats_acum["presiones_contra"].append(s.presiones_visitante or 0)
            stats_acum["posesion"].append(s.posesion_local or 50)
            stats_acum["amarillas_favor"].append(s.amarillas_local or 0)
            stats_acum["rojas_favor"].append(s.rojas_local or 0)
        else:
            stats_acum["xg_favor"].append(s.xg_visitante or 0)
            stats_acum["xg_contra"].append(s.xg_local or 0)
            stats_acum["tiros_favor"].append(s.tiros_visitante or 0)
            stats_acum["tiros_contra"].append(s.tiros_local or 0)
            stats_acum["tiros_arco_favor"].append(s.tiros_arco_visitante or 0)
            stats_acum["tiros_arco_contra"].append(s.tiros_arco_local or 0)
            stats_acum["corners_favor"].append(s.corners_visitante or 0)
            stats_acum["corners_contra"].append(s.corners_local or 0)
            stats_acum["presiones_favor"].append(s.presiones_visitante or 0)
            stats_acum["presiones_contra"].append(s.presiones_local or 0)
            stats_acum["posesion"].append(s.posesion_visitante or 50)
            stats_acum["amarillas_favor"].append(s.amarillas_visitante or 0)
            stats_acum["rojas_favor"].append(s.rojas_visitante or 0)

    if n_con_stats == 0:
        return vacio

    return {
        k: round(sum(v) / len(v), 3) if v else 0.0
        for k, v in stats_acum.items()
    } | {"n_con_stats": n_con_stats}


def calcular_rating_jugadores(db: Session, equipo_id: int,
                               fecha_limite, es_local: bool,
                               n: int = 5) -> dict:
    """
    Rating promedio de los titulares del equipo en sus últimos N
    partidos ANTERIORES a fecha_limite — proxy de calidad de plantilla.

    IMPORTANTE: el rating de Sofascore es una calificación de rendimiento
    calculada DESPUÉS del partido (en base a goles, asistencias, etc).
    Usar el rating del partido que se está prediciendo sería data leakage
    — el modelo "vería" el resultado antes de predecirlo, y en producción
    (partido aún no jugado) esa columna no existe todavía. Por eso acá se
    promedia el rating de partidos PASADOS, igual que calcular_forma.
    """
    if es_local:
        partidos_ids = (
            db.query(Partido.id)
            .filter(
                Partido.equipo_local_id == equipo_id,
                Partido.fecha < fecha_limite,
                Partido.estado == "FT",
                Partido.liga_id.notin_(LIGAS_SIN_HISTORIAL_ID),
            )
            .order_by(Partido.fecha.desc())
            .limit(n)
        )
    else:
        partidos_ids = (
            db.query(Partido.id)
            .filter(
                Partido.equipo_visit_id == equipo_id,
                Partido.fecha < fecha_limite,
                Partido.estado == "FT",
                Partido.liga_id.notin_(LIGAS_SIN_HISTORIAL_ID),
            )
            .order_by(Partido.fecha.desc())
            .limit(n)
        )

    ids = [p.id for p in partidos_ids]
    if not ids:
        return {"rating_promedio": 0.0, "n_jugadores": 0}

    jugadores = (
        db.query(EstadisticaJugador)
        .filter(
            EstadisticaJugador.partido_id.in_(ids),
            EstadisticaJugador.es_local == es_local,
            EstadisticaJugador.titular == True,
            EstadisticaJugador.rating != None,
        )
        .all()
    )

    if not jugadores:
        return {"rating_promedio": 0.0, "n_jugadores": 0}

    ratings = [j.rating for j in jugadores if j.rating]
    return {
        "rating_promedio": round(sum(ratings) / len(ratings), 2),
        "n_jugadores": len(ratings)
    }


def calcular_h2h(db: Session, local_id: int, visit_id: int,
                 fecha_limite, n: int = 5) -> dict:
    partidos = (
        db.query(Partido)
        .filter(
            Partido.equipo_local_id == local_id,
            Partido.equipo_visit_id == visit_id,
            Partido.fecha < fecha_limite,
            Partido.estado == "FT",
            Partido.goles_local != None,
            Partido.liga_id.notin_(LIGAS_SIN_HISTORIAL_ID),
        )
        .order_by(Partido.fecha.desc())
        .limit(n).all()
    )

    if not partidos:
        return {
            "h2h_wins_local": 0, "h2h_empates": 0,
            "h2h_wins_visit": 0, "h2h_goles_local": 0.0,
            "h2h_goles_visit": 0.0, "h2h_n": 0
        }

    wins_l = empates = wins_v = 0
    goles_l = []
    goles_v = []

    for p in partidos:
        gl = p.goles_local     or 0
        gv = p.goles_visitante or 0
        goles_l.append(gl)
        goles_v.append(gv)
        if gl > gv:    wins_l  += 1
        elif gl == gv: empates += 1
        else:          wins_v  += 1

    return {
        "h2h_wins_local":  wins_l,
        "h2h_empates":     empates,
        "h2h_wins_visit":  wins_v,
        "h2h_goles_local": round(sum(goles_l) / len(goles_l), 2),
        "h2h_goles_visit": round(sum(goles_v) / len(goles_v), 2),
        "h2h_n":           len(partidos)
    }


def calcular_win_rate(db: Session, equipo_id: int,
                      fecha_limite, es_local: bool,
                      n: int = 10) -> float:
    if es_local:
        partidos = (
            db.query(Partido)
            .filter(
                Partido.equipo_local_id == equipo_id,
                Partido.fecha < fecha_limite,
                Partido.estado == "FT",
                Partido.goles_local != None,
                Partido.liga_id.notin_(LIGAS_SIN_HISTORIAL_ID),
            )
            .order_by(Partido.fecha.desc())
            .limit(n).all()
        )
    else:
        partidos = (
            db.query(Partido)
            .filter(
                Partido.equipo_visit_id == equipo_id,
                Partido.fecha < fecha_limite,
                Partido.estado == "FT",
                Partido.goles_visitante != None,
                Partido.liga_id.notin_(LIGAS_SIN_HISTORIAL_ID),
            )
            .order_by(Partido.fecha.desc())
            .limit(n).all()
        )

    if not partidos:
        return 0.0

    victorias = 0
    for p in partidos:
        if es_local:
            if (p.goles_local or 0) > (p.goles_visitante or 0):
                victorias += 1
        else:
            if (p.goles_visitante or 0) > (p.goles_local or 0):
                victorias += 1

    return round(victorias / len(partidos), 3)


def construir_features_partido(db: Session,
                                partido: Partido) -> Optional[dict]:
    """
    Construye el vector completo de features para un partido.
    Combina features básicas (forma, H2H, win rate) con
    features avanzadas de Sofascore (xG, presiones, ratings).
    """
    local_id = partido.equipo_local_id
    visit_id = partido.equipo_visit_id
    fecha    = partido.fecha

    # ── Features básicas ──────────────────────────────────
    forma_l  = calcular_forma(db, local_id, fecha, es_local=True,  n=5)
    forma_v  = calcular_forma(db, visit_id, fecha, es_local=False, n=5)

    if forma_l["n_partidos"] < 3 or forma_v["n_partidos"] < 3:
        return None

    wr_local = calcular_win_rate(db, local_id, fecha, es_local=True,  n=10)
    wr_visit = calcular_win_rate(db, visit_id, fecha, es_local=False, n=10)
    h2h      = calcular_h2h(db, local_id, visit_id, fecha, n=5)

    # ── Features Sofascore ────────────────────────────────
    sf_local = calcular_stats_sofascore(db, local_id, fecha,
                                        es_local=True,  n=5)
    sf_visit = calcular_stats_sofascore(db, visit_id, fecha,
                                        es_local=False, n=5)

    # Rating promedio de titulares en los últimos partidos (no del actual —
    # ver comentario en calcular_rating_jugadores sobre data leakage)
    rating_l = calcular_rating_jugadores(
        db, local_id, fecha, es_local=True, n=5)
    rating_v = calcular_rating_jugadores(
        db, visit_id, fecha, es_local=False, n=5)

    # ── Targets ───────────────────────────────────────────
    # resultado: usado por XGBoost. El resto (goles/HT/corners/tarjetas)
    # son para las cabezas extra del MLP multiobjetivo — nunca se usan
    # como feature de entrada, solo como variable a predecir.
    gl = partido.goles_local     or 0
    gv = partido.goles_visitante or 0
    if gl > gv:    resultado = 0   # local gana
    elif gl == gv: resultado = 1   # empate
    else:          resultado = 2   # visitante gana

    resultado_ht = None
    if partido.goles_local_ht is not None and partido.goles_visit_ht is not None:
        ghl, ghv = partido.goles_local_ht, partido.goles_visit_ht
        resultado_ht = 0 if ghl > ghv else (1 if ghl == ghv else 2)

    stats_partido = partido.stats_sofascore
    if isinstance(stats_partido, list):
        stats_partido = stats_partido[0] if stats_partido else None

    corners_total = None
    amarillas_total = None
    if stats_partido:
        if stats_partido.corners_local is not None and stats_partido.corners_visitante is not None:
            corners_total = stats_partido.corners_local + stats_partido.corners_visitante
        if stats_partido.amarillas_local is not None and stats_partido.amarillas_visitante is not None:
            amarillas_total = stats_partido.amarillas_local + stats_partido.amarillas_visitante

    return {
        # Identificadores
        "partido_id":  partido.id,
        "liga_id":     partido.liga_id,
        "temporada":   partido.temporada,
        "fecha":       partido.fecha,

        # Forma básica local
        "forma_local_puntos":  forma_l["puntos"],
        "forma_local_gf":      forma_l["goles_favor"],
        "forma_local_gc":      forma_l["goles_contra"],

        # Forma básica visitante
        "forma_visit_puntos":  forma_v["puntos"],
        "forma_visit_gf":      forma_v["goles_favor"],
        "forma_visit_gc":      forma_v["goles_contra"],

        # Win rates
        "win_rate_local":      wr_local,
        "win_rate_visit":      wr_visit,

        # H2H
        "h2h_wins_local":      h2h["h2h_wins_local"],
        "h2h_empates":         h2h["h2h_empates"],
        "h2h_wins_visit":      h2h["h2h_wins_visit"],
        "h2h_goles_local":     h2h["h2h_goles_local"],
        "h2h_goles_visit":     h2h["h2h_goles_visit"],

        # Sofascore — local
        "xg_favor_local":      sf_local["xg_favor"],
        "xg_contra_local":     sf_local["xg_contra"],
        "tiros_favor_local":   sf_local["tiros_favor"],
        "tiros_arco_fav_local":sf_local["tiros_arco_favor"],
        "corners_fav_local":   sf_local["corners_favor"],
        "presiones_local":     sf_local["presiones_favor"],
        "posesion_local":      sf_local["posesion"],
        "n_stats_local":       sf_local["n_con_stats"],

        # Sofascore — visitante
        "xg_favor_visit":      sf_visit["xg_favor"],
        "xg_contra_visit":     sf_visit["xg_contra"],
        "tiros_favor_visit":   sf_visit["tiros_favor"],
        "tiros_arco_fav_visit":sf_visit["tiros_arco_favor"],
        "corners_fav_visit":   sf_visit["corners_favor"],
        "presiones_visit":     sf_visit["presiones_favor"],
        "posesion_visit":      sf_visit["posesion"],
        "n_stats_visit":       sf_visit["n_con_stats"],

        # Ratings de jugadores
        "rating_local":        rating_l["rating_promedio"],
        "rating_visit":        rating_v["rating_promedio"],

        # Targets
        "resultado":           resultado,
        "goles_local_ft":      gl,
        "goles_visit_ft":      gv,
        "resultado_ht":        resultado_ht,
        "corners_total":       corners_total,
        "amarillas_total":     amarillas_total,
    }