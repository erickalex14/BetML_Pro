"""Features a nivel jugador — para los mercados individuales (tiros,
tiros al arco, goles, tarjetas de jugador).

Mismo principio anti-leakage que calculador.py: todo promedio usa
partidos ANTERIORES a fecha_limite. La diferencia de fondo con el resto
del sistema es que acá no hay "el partido a predecir" con alineación
conocida — Sofascore confirma el XI recién ~1h antes del inicio, así que
para un partido futuro no existe todavía. obtener_titulares_probables()
es la mejor aproximación disponible sin esa información: quién jugó de
titular más seguido en los últimos partidos del equipo.
"""
import logging
from sqlalchemy.orm import Session
from backend.db.modelos import Partido, EstadisticaJugador
from backend.pipeline.config import LIGAS_SIN_HISTORIAL_ID

log = logging.getLogger(__name__)


def obtener_lineup_confirmada(db: Session, partido_id: int, es_local: bool) -> list:
    """XI real confirmado por Sofascore para ESTE partido (job_alineaciones.py
    lo trae ~90 min antes del kickoff) — a diferencia de
    obtener_titulares_probables(), esto no puede listar a un jugador que
    ya se fue del equipo, porque es la alineación real de hoy, no un
    conteo de partidos pasados."""
    filas = (
        db.query(EstadisticaJugador)
        .filter(
            EstadisticaJugador.partido_id == partido_id,
            EstadisticaJugador.es_local == es_local,
            EstadisticaJugador.titular == True,
        )
        .all()
    )
    return [{"sofascore_jugador_id": f.sofascore_jugador_id, "nombre": f.nombre,
             "posicion": f.posicion} for f in filas]


def obtener_titulares_probables(db: Session, equipo_id: int, fecha_limite,
                                 es_local: bool, n_partidos: int = 5,
                                 min_apariciones: float = 0.4) -> list:
    """Jugadores titulares en al menos min_apariciones (40% default) de
    los últimos n_partidos del equipo — el XI probable."""
    if es_local:
        filtro_equipo = Partido.equipo_local_id == equipo_id
    else:
        filtro_equipo = Partido.equipo_visit_id == equipo_id

    partidos_ids = [
        p.id for p in (
            db.query(Partido.id)
            .filter(filtro_equipo, Partido.fecha < fecha_limite, Partido.estado == "FT",
                    Partido.liga_id.notin_(LIGAS_SIN_HISTORIAL_ID))
            .order_by(Partido.fecha.desc())
            .limit(n_partidos)
        )
    ]
    if not partidos_ids:
        return []

    filas = (
        db.query(EstadisticaJugador)
        .filter(
            EstadisticaJugador.partido_id.in_(partidos_ids),
            EstadisticaJugador.es_local == es_local,
            EstadisticaJugador.titular == True,
        )
        .all()
    )

    conteo = {}
    for f in filas:
        clave = f.sofascore_jugador_id
        if clave not in conteo:
            conteo[clave] = {"sofascore_jugador_id": clave, "nombre": f.nombre,
                              "posicion": f.posicion, "titularidades": 0}
        conteo[clave]["titularidades"] += 1

    umbral = min_apariciones * len(partidos_ids)
    return [v for v in conteo.values() if v["titularidades"] >= umbral]


def calcular_forma_jugador(db: Session, sofascore_jugador_id: int, fecha_limite,
                            n: int = 5) -> dict | None:
    """Promedio de stats del jugador en sus últimos n partidos disputados
    antes de fecha_limite (cualquier equipo — un jugador transferido
    sigue siendo el mismo jugador)."""
    filas = (
        db.query(EstadisticaJugador)
        .join(Partido, Partido.id == EstadisticaJugador.partido_id)
        .filter(
            EstadisticaJugador.sofascore_jugador_id == sofascore_jugador_id,
            Partido.fecha < fecha_limite,
            Partido.estado == "FT",
            Partido.liga_id.notin_(LIGAS_SIN_HISTORIAL_ID),
        )
        .order_by(Partido.fecha.desc())
        .limit(n)
        .all()
    )
    if not filas:
        return None

    # OJO: Sofascore omite del JSON los stats de conteo en 0 (no manda
    # "goals": 0, directamente no incluye la clave) — parser.py hace
    # stats.get("goals") sin default, así que None en goles/tiros/
    # tiros_arco significa "0", no "dato faltante". Promediar excluyendo
    # los None infla el promedio de cualquier jugador con pocas
    # apariciones reales del stat (a un jugador con 1 gol en 5 partidos
    # le daba goles_prom=1.0 en vez de 0.2). rating/minutos sí pueden ser
    # None genuinamente (no todos los partidos traen rating), esos se
    # promedian excluyendo nulos.
    def promedio_conteo(attr):
        vals = [getattr(f, attr) or 0 for f in filas]
        return sum(vals) / len(vals)

    def promedio_excluyendo_nulos(attr, default=0.0):
        vals = [getattr(f, attr) for f in filas if getattr(f, attr) is not None]
        return sum(vals) / len(vals) if vals else default

    n_filas = len(filas)
    return {
        "n_partidos": n_filas,
        "tiros_prom": promedio_conteo("tiros"),
        "tiros_arco_prom": promedio_conteo("tiros_arco"),
        "goles_prom": promedio_conteo("goles"),
        "asistencias_prom": promedio_conteo("asistencias"),
        "pases_prom": promedio_conteo("pases_completados"),
        # "Entradas" del bookmaker de referencia — no hay una columna
        # "tackles" separada en Sofascore, duelos_ganados es el proxy más
        # cercano que ya tenemos guardado (duelo defensivo ganado)
        "duelos_prom": promedio_conteo("duelos_ganados"),
        "atajadas_prom": promedio_conteo("atajadas"),
        "prob_amarilla": sum(1 for f in filas if f.amarilla) / n_filas,
        "prob_roja": sum(1 for f in filas if f.roja) / n_filas,
        "minutos_prom": promedio_excluyendo_nulos("minutos_jugados", 90.0),
    }
