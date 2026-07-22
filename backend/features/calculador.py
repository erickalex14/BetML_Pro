import logging
import pandas as pd
from sqlalchemy.orm import Session
from backend.db.modelos import Partido

log = logging.getLogger(__name__)


def calcular_forma(db: Session, equipo_id: int, fecha_limite,
                   es_local: bool, n: int = 5) -> dict:
    """
    Calcula la forma reciente de un equipo en los últimos N partidos
    ANTES de una fecha dada — nunca usa el partido actual.

    es_local=True  → solo partidos donde el equipo jugó en casa
    es_local=False → solo partidos donde el equipo jugó fuera
    Esto es importante porque los equipos se comportan diferente
    en casa vs fuera.

    Retorna un diccionario con:
    - puntos obtenidos (3=victoria, 1=empate, 0=derrota)
    - promedio de goles a favor
    - promedio de goles en contra
    - cantidad de partidos encontrados
    """
    # Filtra partidos del equipo antes de la fecha del partido actual
    if es_local:
        partidos = (
            db.query(Partido)
            .filter(
                Partido.equipo_local_id == equipo_id,
                Partido.fecha < fecha_limite,
                Partido.estado == "FT",
                Partido.goles_local != None
            )
            .order_by(Partido.fecha.desc())
            .limit(n)
            .all()
        )
    else:
        partidos = (
            db.query(Partido)
            .filter(
                Partido.equipo_visit_id == equipo_id,
                Partido.fecha < fecha_limite,
                Partido.estado == "FT",
                Partido.goles_visitante != None
            )
            .order_by(Partido.fecha.desc())
            .limit(n)
            .all()
        )

    if not partidos:
        # Si no hay partidos históricos, retorna valores neutros
        return {
            "puntos":         0,
            "goles_favor":    0.0,
            "goles_contra":   0.0,
            "n_partidos":     0
        }

    puntos = 0
    goles_favor  = []
    goles_contra = []

    for p in partidos:
        if es_local:
            gf = p.goles_local     or 0
            gc = p.goles_visitante or 0
            if gf > gc:   puntos += 3
            elif gf == gc: puntos += 1
        else:
            gf = p.goles_visitante or 0
            gc = p.goles_local     or 0
            if gf > gc:   puntos += 3
            elif gf == gc: puntos += 1

        goles_favor.append(gf)
        goles_contra.append(gc)

    return {
        "puntos":       puntos,
        "goles_favor":  round(sum(goles_favor)  / len(goles_favor),  2),
        "goles_contra": round(sum(goles_contra) / len(goles_contra), 2),
        "n_partidos":   len(partidos)
    }


def calcular_h2h(db: Session, local_id: int, visit_id: int,
                 fecha_limite, n: int = 5) -> dict:
    """
    Calcula el historial de enfrentamientos directos (H2H)
    entre dos equipos antes de una fecha dada.

    Retorna victorias, empates, derrotas y promedio de goles
    desde la perspectiva del equipo local.
    """
    partidos = (
        db.query(Partido)
        .filter(
            Partido.equipo_local_id == local_id,
            Partido.equipo_visit_id == visit_id,
            Partido.fecha < fecha_limite,
            Partido.estado == "FT",
            Partido.goles_local != None
        )
        .order_by(Partido.fecha.desc())
        .limit(n)
        .all()
    )

    if not partidos:
        return {
            "h2h_victorias_local":  0,
            "h2h_empates":          0,
            "h2h_victorias_visit":  0,
            "h2h_goles_local":      0.0,
            "h2h_goles_visit":      0.0,
            "h2h_n_partidos":       0
        }

    victorias_l = 0
    empates     = 0
    victorias_v = 0
    goles_l     = []
    goles_v     = []

    for p in partidos:
        gl = p.goles_local     or 0
        gv = p.goles_visitante or 0
        goles_l.append(gl)
        goles_v.append(gv)

        if gl > gv:   victorias_l += 1
        elif gl == gv: empates    += 1
        else:          victorias_v += 1

    return {
        "h2h_victorias_local": victorias_l,
        "h2h_empates":         empates,
        "h2h_victorias_visit": victorias_v,
        "h2h_goles_local":     round(sum(goles_l) / len(goles_l), 2),
        "h2h_goles_visit":     round(sum(goles_v) / len(goles_v), 2),
        "h2h_n_partidos":      len(partidos)
    }


def calcular_win_rate(db: Session, equipo_id: int,
                      fecha_limite, es_local: bool,
                      n: int = 10) -> float:
    """
    Calcula el porcentaje de victorias de un equipo
    en los últimos N partidos antes de una fecha.

    es_local=True  → rendimiento en casa
    es_local=False → rendimiento fuera
    """
    if es_local:
        partidos = (
            db.query(Partido)
            .filter(
                Partido.equipo_local_id == equipo_id,
                Partido.fecha < fecha_limite,
                Partido.estado == "FT",
                Partido.goles_local != None
            )
            .order_by(Partido.fecha.desc())
            .limit(n)
            .all()
        )
    else:
        partidos = (
            db.query(Partido)
            .filter(
                Partido.equipo_visit_id == equipo_id,
                Partido.fecha < fecha_limite,
                Partido.estado == "FT",
                Partido.goles_visitante != None
            )
            .order_by(Partido.fecha.desc())
            .limit(n)
            .all()
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


def construir_features_partido(db: Session, partido: Partido) -> dict | None:
    """
    Función principal — construye el vector de features
    completo para un partido dado.

    Retorna None si no hay suficientes datos históricos
    (menos de 3 partidos anteriores de alguno de los equipos).
    """
    local_id  = partido.equipo_local_id
    visit_id  = partido.equipo_visit_id
    fecha     = partido.fecha

    # Forma reciente local (jugando en casa)
    forma_l = calcular_forma(db, local_id, fecha, es_local=True,  n=5)
    # Forma reciente visitante (jugando fuera)
    forma_v = calcular_forma(db, visit_id, fecha, es_local=False, n=5)

    # Descarta partidos sin suficiente historial
    if forma_l["n_partidos"] < 3 or forma_v["n_partidos"] < 3:
        return None

    # Win rate en últimos 10 partidos
    wr_local = calcular_win_rate(db, local_id, fecha, es_local=True,  n=10)
    wr_visit = calcular_win_rate(db, visit_id, fecha, es_local=False, n=10)

    # H2H
    h2h = calcular_h2h(db, local_id, visit_id, fecha, n=5)

    # Target — lo que el modelo va a predecir
    # 0 = local gana, 1 = empate, 2 = visitante gana
    gl = partido.goles_local     or 0
    gv = partido.goles_visitante or 0

    if gl > gv:    resultado = 0
    elif gl == gv: resultado = 1
    else:          resultado = 2

    return {
        # Identificadores (no son features del modelo)
        "partido_id":           partido.id,
        "liga_id":              partido.liga_id,
        "temporada":            partido.temporada,
        "fecha":                partido.fecha,

        # Features de forma local
        "forma_local_puntos":   forma_l["puntos"],
        "forma_local_gf":       forma_l["goles_favor"],
        "forma_local_gc":       forma_l["goles_contra"],

        # Features de forma visitante
        "forma_visit_puntos":   forma_v["puntos"],
        "forma_visit_gf":       forma_v["goles_favor"],
        "forma_visit_gc":       forma_v["goles_contra"],

        # Win rates
        "win_rate_local":       wr_local,
        "win_rate_visit":       wr_visit,

        # H2H
        "h2h_wins_local":       h2h["h2h_victorias_local"],
        "h2h_empates":          h2h["h2h_empates"],
        "h2h_wins_visit":       h2h["h2h_victorias_visit"],
        "h2h_goles_local":      h2h["h2h_goles_local"],
        "h2h_goles_visit":      h2h["h2h_goles_visit"],

        # Target
        "resultado":            resultado,
    }