import json
import logging
from typing import Optional, List
from backend.db.modelos import EstadisticaSofascore, EstadisticaJugador

log = logging.getLogger(__name__)


def parsear_stats_partido(
        partido_id: int,
        sofascore_id:int,
        stats_raw: list
) -> Optional[EstadisticaSofascore]:
    """
    Convierte el JSON de estadísticas de Sofascore
    en un objeto EstadisticaSofascore listo para guardar.

    stats_raw es una lista de grupos de estadísticas:
    [
      {
        "period": "ALL",
        "groups": [
          {
            "groupName": "Shots",
            "statisticsItems": [
              {"name": "Total Shots", "home": "12", "away": "8"},
              ...
            ]
          }
        ]
      }
    ]
    """
    if not stats_raw:
        return None


    #Busca el periodo ALL (Estadisticas totales del partido)
    stats_all = next(
        (s for s in stats_raw if s.get("period")  == "ALL"),
        None
    )
    if not stats_all:
        #Si no hay ALL, usa el primer periodo disponible
        stats_all = stats_raw[0] if stats_raw else None

    if not stats_all:
        return None

    #Diccionario plano de facil acceso
    stats = {}
    for grupo in stats_all.get("groups", []):
        for item in grupo.get("statisticsItems", []):
            nombre = item.get("name", "")
            home = item.get("home")
            away = item.get("away")
            stats[nombre] = {"home": home, "away": away}

    def val(nombre: str, equipo: str) -> Optional[float]:
        """Extrae valor numérico de una estadística."""
        item = stats.get(nombre, {})
        raw = item.get(equipo)
        if raw is None:
            return None
        try:
            # Algunos valores vienen como "45%" o "12.3"
            cleaned = str(raw).replace("%", "").strip()
            return float(cleaned)
        except(ValueError, TypeError):
            return None

    return EstadisticaSofascore(
        partido_id=partido_id,
        sofascore_id=sofascore_id,

        #xg
        xg_local = val("Expected goals", "home"),
        xg_visitante = val("Expected goals", "away"),

        #Tiros
        tiros_local= val("Total shoots", "home"),
        tiros_visitante= val("Total shoots", "away"),
        tiros_arco_local= val("Shoots on target", "home"),
        tiros_arco_visitante= val("Shoots on target", "away"),
        tiros_bloq_local= val("Blocked shoots", "home"),
        tiros_bloq_visitante= val("Blocked shoots", "away"),

        #Posesion
        posesion_local= val("Ball possession", "home"),
        posesion_visitante= val("Ball possession", "away"),

        #pases
        pases_local= val("Total passes", "home"),
        pases_visitante= val("Total passes", "away"),
        precision_pases_local= val("Acurate passes", "home"),
        precision_pases_visitante= val("Acurate passes", "away"),
        pases_clave_local= val("Key passes", "home"),
        pases_clave_visitante= val("Key passes", "away"),

        #Corners y faltas
        corners_local= val("Corner kicks", "home"),
        corners_visitante= val("Corner kicks", "away"),
        faltas_local= val("Fouls", "home"),
        faltas_visitante= val("Fouls", "away"),

        #Presiones
        presiones_local= val("Pressures", "home"),
        presiones_visitante= val("Pressures", "away"),

        #Duelos
        duelos_local= val("Ground duels won", "home"),
        duelos_visitante= val("Ground duels won", "away"),
        duelos_aereos_local= val("Aerial duels won", "away"),
        duelos_aereos_visitante= val("Aerial duels won", "away"),

        #Tarjetas
        amarillas_local= val("Yellow Cards", "home"),
        amarillas_visitante= val("Yellow Cards", "away"),
        rojas_local= val("Red Cards", "home"),
        rojas_visitante= val("Red Cards", "away"),

        #Offisdes
        fuera_juego_local= val("Offsides", "home"),
        fuera_juego_visitante= val("Offsides", "away"),
    )

def parsear_jugadores(
    partido_id: int,
    lineups_raw: dict
) -> list:
    """
        Convierte las alineaciones de Sofascore en objetos
        EstadisticaJugador listos para guardar en BD.
        """
    jugadores = []

    for es_local, clave in [(True, "home"), (False, "away")]:
        equipo_data = lineups_raw.get(clave, {})
        equipo_id = equipo_data.get("team", {}).get("id")
        players = equipo_data.get("players", [])

        for p in players:
            jugador = p.get("player", {})
            stats = p.get("statistics", {})

            jugadores.append(EstadisticaJugador(
                partido_id=partido_id,
                equipo_id=equipo_id,
                sofascore_jugador_id=jugador.get("id", 0),
                nombre=jugador.get("name", ""),
                posicion=p.get("position"),
                es_local=es_local,
                titular=p.get("substitute", True) == False,

                # Rating
                rating=stats.get("rating"),

                # Participación
                minutos_jugados=stats.get("minutesPlayed"),

                # Ataque
                goles=stats.get("goals"),
                asistencias=stats.get("goalAssist"),
                xg_individual=stats.get("expectedGoals"),
                tiros=stats.get("totalShots"),
                tiros_arco=stats.get("shotsOnTarget"),

                # Creación
                pases_clave=stats.get("keyPass"),
                grandes_ocasiones=stats.get("bigChanceCreated"),
                regates_completados=stats.get("successfulDribbles"),

                # Pases
                pases_completados=stats.get("accuratePass"),
                precision_pases=stats.get("accurateLongBalls"),

                # Defensa
                duelos_ganados=stats.get("duelWon"),
                duelos_aereos_gan=stats.get("aerialWon"),
                despejes=stats.get("clearanceOffLine"),
                intercepciones=stats.get("interceptionWon"),

                # Disciplina
                amarilla=bool(stats.get("yellowCard")),
                roja=bool(stats.get("redCard")),
            ))

    return jugadores


