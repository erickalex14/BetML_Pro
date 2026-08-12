"""Trae la alineación CONFIRMADA de Sofascore para partidos que arrancan
pronto — corrige el bug real de "jugador que ya se fue sigue apareciendo":
obtener_titulares_probables() (features/jugadores.py) es un heurístico
sobre partidos pasados, no sabe de transferencias. Sofascore confirma el
XI real ~60-90 min antes del kickoff; en cuanto está, jugadores.py la usa
en vez del heurístico (ver obtener_lineup_confirmada()).

Antes de pedir la alineación hace falta el sofascore_id del partido —
los partidos que llegan solo por pipeline_dia (API-Football) nunca lo
tienen, ninguna otra corrida los ancla el mismo día. Por eso este job
primero intenta ANCLAR el id cruzando la página 0 (eventos más
recientes) de la liga+temporada de Sofascore correspondiente —
TEMPORADAS_HISTORICAS, el mismo mapeo que ya usa job_sofascore.py — por
nombre de equipo, mismo principio que job_historico_sofascore.py pero
en la dirección inversa (acá partimos de un Partido sin id).

El endpoint por FECHA de Sofascore (/scheduled-events/{fecha}) está
muerto — 404 confirmado en vivo, ya documentado en job_sofascore.py —
por eso no se usa acá tampoco.

Límite real: TEMPORADAS_HISTORICAS solo cubre ligas oficiales. Amistosos
("Friendlies"/"Friendlies Clubs", agregados a LIGAS hoy) no tienen
liga_id de Sofascore mapeado — para esos partidos este job no puede
anclar el id, así que siguen con el heurístico de jugadores.py (con el
mismo riesgo de listar a alguien transferido) hasta que se agregue esa
liga al mapeo.

Costo: cada corrida abre un browser Chromium real (Playwright, ver
cliente.py) — lento pero SIN costo de cuota de API-Football (Sofascore no
comparte ese límite de 100 requests/día). Se agenda cada 15 min junto con
job_partidos_en_vivo; solo hace trabajo real si hay un partido dentro de
la ventana y todavía sin alineación confirmada guardada.
"""
import logging
from datetime import datetime, timedelta
from backend.db.database import SessionLocal
from backend.db.modelos import Partido, Equipo, EstadisticaJugador
from backend.pipeline.config import ahora_partidos

log = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

_ESTADOS_ELEGIBLES = ("NS", "1H", "HT", "2H", "ET")
VENTANA_MINUTOS = 90


def _partidos_elegibles(db) -> list:
    """Partidos dentro de la ventana, sin importar si ya tienen
    sofascore_id — eso se resuelve (o no) en _anclar_sofascore_ids."""
    ahora = ahora_partidos()
    limite = ahora + timedelta(minutes=VENTANA_MINUTOS)

    candidatos = (
        db.query(Partido)
        .filter(
            Partido.estado.in_(_ESTADOS_ELEGIBLES),
            Partido.fecha <= limite,
        )
        .all()
    )

    pendientes = []
    for p in candidatos:
        ya_confirmada = (
            db.query(EstadisticaJugador)
            .filter(EstadisticaJugador.partido_id == p.id, EstadisticaJugador.titular.is_(True))
            .first()
        )
        if ya_confirmada is None:
            pendientes.append(p)
    return pendientes


def _nombre_coincide(a: str, b: str) -> bool:
    a, b = a.lower().strip(), b.lower().strip()
    return a in b or b in a


def _anclar_sofascore_ids(db, cliente, partidos: list) -> None:
    """Para cada partido sin sofascore_id, busca su liga en
    TEMPORADAS_HISTORICAS y cruza la página 0 (eventos más recientes,
    incluye los que todavía no arrancaron) de esa liga+temporada por
    nombre de equipo. Un solo fetch por liga presente entre los
    partidos pendientes, no uno por partido."""
    from backend.pipeline.sofascore.cliente import TEMPORADAS_HISTORICAS
    from backend.db.modelos import Liga

    sin_id = [p for p in partidos if not p.sofascore_id]
    if not sin_id:
        return

    ligas_pendientes = {p.liga_id for p in sin_id}
    eventos_por_liga = {}

    for liga_id_local in ligas_pendientes:
        liga = db.get(Liga, liga_id_local)
        if not liga:
            continue
        entradas = [t for t in TEMPORADAS_HISTORICAS if t[0] == liga.nombre]
        if not entradas:
            log.info(f"'{liga.nombre}' sin liga+temporada de Sofascore mapeada — sin anclar")
            continue
        # última temporada listada = la vigente (TEMPORADAS_HISTORICAS
        # está ordenada de más vieja a más nueva por liga)
        _, sofa_liga_id, season_id, _ = entradas[-1]
        eventos = cliente.get_proximos_partidos_liga_temporada(liga_id=sofa_liga_id, temporada_id=season_id, pagina=0)
        eventos_por_liga[liga_id_local] = eventos or []

    ya_usados = set()  # sofascore_id ya asignado EN ESTA CORRIDA — evita
                        # que dos partidos nuestros (mismos 2 equipos,
                        # fecha distinta — se enfrentan varias veces por
                        # temporada) reclamen el mismo evento

    for partido in sin_id:
        eventos = eventos_por_liga.get(partido.liga_id)
        if not eventos:
            continue
        local = db.get(Equipo, partido.equipo_local_id)
        visit = db.get(Equipo, partido.equipo_visit_id)
        if not local or not visit:
            continue

        for evento in eventos:
            sofascore_id = evento.get("id")
            if sofascore_id in ya_usados:
                continue

            # incluye fecha, no solo nombre — dos equipos que se cruzan
            # más de una vez en la temporada (ida/vuelta, distintas
            # fechas) no deben resolver al mismo evento (bug real
            # encontrado: LDU vs Independiente del Valle, dos fechas
            # distintas, matcheaban ambas al mismo evento por nombre)
            timestamp = evento.get("startTimestamp")
            if timestamp is None:
                continue
            fecha_evento = datetime.fromtimestamp(timestamp).date()
            if fecha_evento != partido.fecha.date():
                continue

            home = evento.get("homeTeam", {}).get("name", "")
            away = evento.get("awayTeam", {}).get("name", "")
            if _nombre_coincide(local.nombre, home) and _nombre_coincide(visit.nombre, away):
                # guard final: puede que otro Partido YA guardado (no
                # solo los de esta corrida) tenga este id de una corrida
                # anterior — sofascore_id es UNIQUE, un duplicado acá
                # tira IntegrityError y aborta el commit de todo el lote
                if db.query(Partido).filter(Partido.sofascore_id == sofascore_id).first():
                    continue
                partido.sofascore_id = sofascore_id
                ya_usados.add(sofascore_id)
                log.info(f"sofascore_id anclado — partido {partido.id} ({local.nombre} vs {visit.nombre})")
                break

    db.commit()


def correr_job_alineaciones():
    db = SessionLocal()
    try:
        elegibles = _partidos_elegibles(db)
        if not elegibles:
            log.info("Sin partidos por confirmar alineación")
            return

        from backend.pipeline.sofascore.cliente import SofascoreCliente
        from backend.pipeline.sofascore.parser import parsear_jugadores
        from backend.pipeline.sofascore.guardador_sofascore import guardar_jugadores

        log.info(f"{len(elegibles)} partido(s) por confirmar alineación")
        with SofascoreCliente() as cliente:
            _anclar_sofascore_ids(db, cliente, elegibles)

            for partido in elegibles:
                if not partido.sofascore_id:
                    log.info(f"partido {partido.id} sin match en Sofascore hoy — se reintenta en 15 min")
                    continue

                lineups_raw = cliente.get_lineups_partido(partido.sofascore_id)
                if not lineups_raw:
                    continue  # todavía no la publicó — se reintenta en 15 min

                jugadores = parsear_jugadores(
                    partido.id, lineups_raw,
                    partido.equipo_local_id, partido.equipo_visit_id)
                if jugadores:
                    guardar_jugadores(db, jugadores, partido.id)
                    log.info(f"Alineación confirmada — partido {partido.id}")
    finally:
        db.close()


if __name__ == "__main__":
    correr_job_alineaciones()
