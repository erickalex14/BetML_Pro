import logging
from typing import Optional
from backend.db.modelos import EstadisticaSofascore, EstadisticaJugador

log = logging.getLogger(__name__)


def _extraer_valor(stats: dict, nombre: str) -> Optional[float]:
    """
    Extrae un valor numérico de las estadísticas.
    Maneja formatos especiales:
      "54%"        → 54.0
      "27/47 (57%)"→ 57.0 (el porcentaje)
      "0.63"       → 0.63
      None         → None
    """
    item = stats.get(nombre, {})
    if not item:
        return None

    for equipo in ["home", "away"]:
        # Solo procesamos el valor, no importa qué equipo
        pass

    return None


def _build_stats_dict(stats_raw: list) -> tuple:
    """
    Construye dos diccionarios planos de stats:
    uno para local (home) y uno para visitante (away).
    """
    home_stats = {}
    away_stats = {}

    stats_all = next(
        (s for s in stats_raw if s.get("period") == "ALL"),
        stats_raw[0] if stats_raw else None
    )

    if not stats_all:
        return home_stats, away_stats

    for grupo in stats_all.get("groups", []):
        for item in grupo.get("statisticsItems", []):
            nombre = item.get("name", "")
            home_raw = item.get("home")
            away_raw = item.get("away")

            home_stats[nombre] = _limpiar_valor(home_raw)
            away_stats[nombre] = _limpiar_valor(away_raw)

    return home_stats, away_stats


def _limpiar_valor(raw) -> Optional[float]:
    """
    Limpia y convierte cualquier valor de Sofascore a float.
    Maneja: None, "54%", "27/47 (57%)", "0.63", 7
    """
    if raw is None:
        return None

    raw_str = str(raw).strip()

    # Formato "27/47 (57%)" → extrae el porcentaje
    if "(" in raw_str and "%" in raw_str:
        try:
            inicio = raw_str.index("(") + 1
            fin    = raw_str.index("%")
            return float(raw_str[inicio:fin])
        except (ValueError, IndexError):
            return None

    # Formato "54%" → 54.0
    if "%" in raw_str:
        try:
            return float(raw_str.replace("%", "").strip())
        except ValueError:
            return None

    # Número directo
    try:
        return float(raw_str)
    except ValueError:
        return None


def parsear_stats_partido(
    partido_id: int,
    sofascore_id: int,
    stats_raw: list
) -> Optional[EstadisticaSofascore]:
    """
    Convierte las estadísticas de Sofascore en un objeto
    EstadisticaSofascore con los nombres de campos correctos.
    """
    if not stats_raw:
        return None

    home, away = _build_stats_dict(stats_raw)

    if not home and not away:
        return None

    return EstadisticaSofascore(
        partido_id=partido_id,
        sofascore_id=sofascore_id,
        xg_local=home.get("Expected goals"),
        xg_visitante=away.get("Expected goals"),
        tiros_local=home.get("Total shots"),
        tiros_visitante=away.get("Total shots"),
        tiros_arco_local=home.get("Shots on target"),
        tiros_arco_visitante=away.get("Shots on target"),
        tiros_bloq_local=home.get("Blocked shots"),
        tiros_bloq_visitante=away.get("Blocked shots"),
        posesion_local=home.get("Ball possession"),
        posesion_visitante=away.get("Ball possession"),
        pases_local=home.get("Passes"),
        pases_visitante=away.get("Passes"),
        precision_pases_local=home.get("Accurate passes"),
        precision_pases_visitante=away.get("Accurate passes"),
        pases_clave_local=home.get("Key passes"),
        pases_clave_visitante=away.get("Key passes"),
        corners_local=home.get("Corner kicks"),
        corners_visitante=away.get("Corner kicks"),
        faltas_local=home.get("Fouls"),
        faltas_visitante=away.get("Fouls"),
        presiones_local=home.get("Pressures"),
        presiones_visitante=away.get("Pressures"),
        duelos_local=home.get("Ground duels"),
        duelos_visitante=away.get("Ground duels"),
        duelos_aereos_local=home.get("Aerial duels"),
        duelos_aereos_visitante=away.get("Aerial duels"),
        amarillas_local=home.get("Yellow cards"),
        amarillas_visitante=away.get("Yellow cards"),
        rojas_local=home.get("Red cards"),
        rojas_visitante=away.get("Red cards"),
        fuera_juego_local=home.get("Offsides"),
        fuera_juego_visitante=away.get("Offsides"),
    )


def parsear_jugadores(
    partido_id: int,
    lineups_raw: dict,
    equipo_local_id: int,
    equipo_visit_id: int,
) -> list:
    """
    Convierte las alineaciones de Sofascore en objetos
    EstadisticaJugador listos para guardar en BD.

    equipo_local_id/equipo_visit_id: id INTERNO (equipos.id, no el de
    Sofascore) — antes esto intentaba leer equipo_data["team"]["id"] del
    payload de Sofascore, que (a) es el id de Sofascore, no el nuestro —
    mismo espacio de numeración que el resto del proyecto ya tuvo que
    separar en una columna sofascore_id aparte — y (b) esa clave ni
    siquiera existe en el JSON real de /lineups, por eso equipo_id salía
    NULL en el 100% de las 695k filas ya guardadas.
    """
    jugadores = []

    for es_local, clave in [(True, "home"), (False, "away")]:
        equipo_data = lineups_raw.get(clave, {})
        equipo_id   = equipo_local_id if es_local else equipo_visit_id
        players     = equipo_data.get("players", [])

        for p in players:
            jugador = p.get("player", {})
            stats   = p.get("statistics", {})

            # substitute=False significa que ES titular
            es_titular = not p.get("substitute", True)

            jugadores.append(EstadisticaJugador(
                partido_id           = partido_id,
                equipo_id            = equipo_id,
                sofascore_jugador_id = jugador.get("id", 0),
                nombre               = jugador.get("name", ""),
                posicion             = p.get("position"),
                es_local             = es_local,
                titular              = es_titular,

                rating               = stats.get("rating"),
                minutos_jugados      = stats.get("minutesPlayed"),

                goles                = stats.get("goals"),
                asistencias          = stats.get("goalAssist"),
                xg_individual        = stats.get("expectedGoals"),
                tiros                = stats.get("totalShots"),
                tiros_arco           = stats.get("shotsOnTarget"),
                atajadas             = stats.get("saves"),

                pases_clave          = stats.get("keyPass"),
                grandes_ocasiones    = stats.get("bigChanceCreated"),
                regates_completados  = stats.get("successfulDribbles"),

                pases_completados    = stats.get("accuratePass"),
                precision_pases      = stats.get("accurateLongBalls"),

                duelos_ganados       = stats.get("duelWon"),
                duelos_aereos_gan    = stats.get("aerialWon"),
                despejes             = stats.get("clearanceOffLine"),
                intercepciones       = stats.get("interceptionWon"),

                amarilla             = bool(stats.get("yellowCard")),
                roja                 = bool(stats.get("redCard")),
            ))

    return jugadores