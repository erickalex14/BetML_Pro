"""Trae la alineación CONFIRMADA de Sofascore para partidos que arrancan
pronto — corrige el bug real de "jugador que ya se fue sigue apareciendo":
obtener_titulares_probables() (features/jugadores.py) es un heurístico
sobre partidos pasados, no sabe de transferencias. Sofascore confirma el
XI real ~60-90 min antes del kickoff; en cuanto está, jugadores.py la usa
en vez del heurístico (ver obtener_lineup_confirmada()).

Antes de pedir la alineación hace falta el sofascore_id del partido —
los partidos que llegan solo por pipeline_dia (API-Football) nunca lo
tienen, ninguna otra corrida los ancla el mismo día. Por eso este job
primero intenta ANCLAR el id cruzando los eventos de esa liga en esa
fecha (get_partidos_liga_fecha en cliente.py) por nombre de equipo —
mismo principio que job_historico_sofascore.py pero en la dirección
inversa (acá partimos de un Partido sin id).

Ojo con los endpoints de Sofascore: /sport/football/scheduled-events/
{fecha} da 404 (probado en api. y en www.), y /events/next/ también.
El que sí funciona es /unique-tournament/{id}/scheduled-events/{fecha},
sacado del tráfico real de su web.

Límite real: LIGAS_SOFASCORE solo cubre las ligas ahí mapeadas.
Amistosos ("Friendlies"/"Friendlies Clubs") y torneos sueltos como la
UEFA Super Cup no tienen id de torneo de Sofascore mapeado — para esos
partidos este job no puede anclar el id, así que siguen con el
heurístico de jugadores.py (con el mismo riesgo de listar a alguien
transferido) hasta que se agregue esa liga al mapeo.

Costo: cada corrida abre un browser Chromium real (Playwright, ver
cliente.py) — lento pero SIN costo de cuota de API-Football (Sofascore no
comparte ese límite de 100 requests/día). Se agenda cada 15 min junto con
job_partidos_en_vivo; solo hace trabajo real si hay un partido dentro de
la ventana y todavía sin alineación confirmada guardada.
"""
import logging
import unicodedata
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


def _partidos_a_anclar(db) -> list:
    """TODOS los partidos de hoy sin sofascore_id — no solo los de la
    ventana de 90 min. El anclaje cuesta un fetch por (liga, fecha), no
    uno por partido, así que anclar el día entero sale prácticamente lo
    mismo que anclar los 2 que arrancan ya; y hace falta el día entero
    porque job_sofascore_en_vivo.py necesita el id de CUALQUIER partido
    que esté en vivo, no solo de los que están por empezar (con la
    ventana sola quedaba 4/33 anclados)."""
    ahora = ahora_partidos()
    inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    fin = inicio + timedelta(days=1)
    return (
        db.query(Partido)
        .filter(
            Partido.sofascore_id.is_(None),
            Partido.fecha >= inicio,
            Partido.fecha < fin,
        )
        .all()
    )


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


def _normalizar(nombre: str) -> str:
    """minúsculas, sin acentos, sin puntuación, espacios colapsados.

    Sin esto el cruce falla por diferencias cosméticas entre las dos
    fuentes: "Paris Saint Germain" (API-Football, nuestra BD) no es
    substring de "Paris Saint-Germain" (Sofascore) por el guion, y lo
    mismo pasa con acentos ("Bolívar"/"Bolivar", "Atlético"/"Atletico").
    Casos reales: por esto quedaban partidos sin anclar aunque el evento
    existía en Sofascore."""
    sin_acentos = unicodedata.normalize("NFKD", nombre)
    sin_acentos = "".join(c for c in sin_acentos if not unicodedata.combining(c))
    solo_alfanum = "".join(c if c.isalnum() else " " for c in sin_acentos.lower())
    return " ".join(solo_alfanum.split())


# Ruido que las dos fuentes escriben distinto para el MISMO club
_RUIDO_EQUIPO = {
    "fc", "cf", "sc", "ac", "afc", "cd", "ca", "club", "de", "del", "la", "el",
    "los", "las", "do", "da", "of", "the", "and", "y", "sv", "vf", "vfl", "vfb",
}


def _tokens_equipo(nombre: str) -> set:
    """Palabras significativas del nombre de un equipo — sin acentos, sin
    puntuación, sin ruido y sin números sueltos ("Bayer 04 Leverkusen")."""
    return {
        t for t in _normalizar(nombre).split()
        if t not in _RUIDO_EQUIPO and not t.isdigit()
    }


def _nombre_coincide(a: str, b: str) -> bool:
    """True si los dos nombres son del mismo equipo.

    Compara CONJUNTOS de palabras, no substrings: las dos fuentes meten
    palabras distintas en el medio y el substring falla aunque el equipo
    sea obviamente el mismo. Casos reales que quedaban sin anclar el
    2026-08-12: "Bayer Leverkusen" vs "Bayer 04 Leverkusen" y
    "Deportivo La Coruna" vs "Deportivo de A Coruña".

    Acepta si un conjunto está contenido en el otro — no exige igualdad,
    porque una fuente suele ser más verbosa que la otra."""
    ta, tb = _tokens_equipo(a), _tokens_equipo(b)
    if not ta or not tb:
        return False
    return ta <= tb or tb <= ta


def _intentar_match(db, partido, eventos: list, ya_usados: set) -> bool:
    """Busca el evento de Sofascore que corresponde a este partido y le
    pega el sofascore_id. True si lo ancló."""
    local = db.get(Equipo, partido.equipo_local_id)
    visit = db.get(Equipo, partido.equipo_visit_id)
    if not local or not visit:
        return False

    for evento in eventos:
        sofascore_id = evento.get("id")
        if not sofascore_id or sofascore_id in ya_usados:
            continue

        # incluye fecha, no solo nombre — dos equipos que se cruzan más
        # de una vez en la temporada (ida/vuelta, distintas fechas) no
        # deben resolver al mismo evento (bug real encontrado: LDU vs
        # Independiente del Valle, dos fechas distintas, matcheaban
        # ambas al mismo evento por nombre)
        timestamp = evento.get("startTimestamp")
        if timestamp is None:
            continue
        if datetime.fromtimestamp(timestamp).date() != partido.fecha.date():
            continue

        home = evento.get("homeTeam", {}).get("name", "")
        away = evento.get("awayTeam", {}).get("name", "")
        if _nombre_coincide(local.nombre, home) and _nombre_coincide(visit.nombre, away):
            # guard final: puede que otro Partido YA guardado (no solo
            # los de esta corrida) tenga este id de una corrida anterior
            # — sofascore_id es UNIQUE, un duplicado acá tira
            # IntegrityError y aborta el commit de todo el lote
            if db.query(Partido).filter(Partido.sofascore_id == sofascore_id).first():
                continue
            partido.sofascore_id = sofascore_id
            ya_usados.add(sofascore_id)
            log.info(f"sofascore_id anclado — partido {partido.id} ({local.nombre} vs {visit.nombre})")
            return True
    return False


def _anclar_sofascore_ids(db, cliente, partidos: list) -> None:
    """Para cada partido sin sofascore_id, trae los eventos de SU liga en
    SU fecha desde Sofascore y los cruza por nombre de equipo + fecha.

    Dos pasadas:
      1. Ids de torneo YA conocidos — los fijos de LIGAS_SOFASCORE más
         los que el descubridor aprendió antes (tabla LigaSofascoreTorneo).
      2. Descubrimiento, solo para los que quedaron sin anclar: busca
         entre los torneos del día uno cuyo nombre se parezca al de la
         liga y prueba ahí (ver descubridor_torneos.py). Lo que encuentra
         queda guardado, así la próxima corrida ya entra por la pasada 1.

    Hace falta la pasada 2 porque una liga nuestra puede vivir en varios
    torneos de Sofascore: las fases de clasificación tienen id propio,
    distinto al de la fase principal, y los amistosos están repartidos
    en varios torneos.

    Usa /unique-tournament/{id}/scheduled-events/{fecha} (ver
    get_partidos_liga_fecha en cliente.py) — endpoint sacado del tráfico
    real de sofascore.com. La versión anterior usaba /events/next/, que
    devuelve 404: por eso el anclaje no funcionaba para NINGÚN partido
    del día (0/33 medido el 2026-08-12) y todo lo que depende del
    sofascore_id — alineación confirmada, stats en vivo — quedaba muerto.
    """
    from backend.pipeline.sofascore.cliente import LIGAS_SOFASCORE
    from backend.pipeline.sofascore.descubridor_torneos import (
        torneos_conocidos, recordar_torneo, torneos_del_dia, filtrar_candidatos)
    from backend.db.modelos import Liga

    sin_id = [p for p in partidos if not p.sofascore_id]
    if not sin_id:
        return

    ya_usados = set()  # sofascore_id ya asignado EN ESTA CORRIDA
    eventos_cache = {}  # (torneo_id, fecha) -> eventos, un fetch por clave

    def eventos_de(torneo_id, fecha):
        clave = (torneo_id, fecha)
        if clave not in eventos_cache:
            eventos_cache[clave] = cliente.get_partidos_liga_fecha(torneo_id, str(fecha)) or []
        return eventos_cache[clave]

    # ── Pasada 1: ids conocidos ────────────────────────────────
    pendientes = []
    for partido in sin_id:
        liga = db.get(Liga, partido.liga_id)
        if not liga:
            continue
        ids = []
        fijo = LIGAS_SOFASCORE.get(liga.nombre)
        if fijo:
            ids.append(fijo)
        ids.extend(t for t in torneos_conocidos(db, liga.id) if t not in ids)

        anclado = any(
            _intentar_match(db, partido, eventos_de(tid, partido.fecha.date()), ya_usados)
            for tid in ids
        )
        if not anclado:
            pendientes.append((partido, liga))
    db.commit()

    # ── Pasada 2: descubrimiento ───────────────────────────────
    torneos_cache = {}  # fecha -> lista completa de torneos de ese día
    for partido, liga in pendientes:
        fecha = partido.fecha.date()
        if fecha not in torneos_cache:
            torneos_cache[fecha] = torneos_del_dia(cliente, str(fecha))
        candidatos = filtrar_candidatos(torneos_cache[fecha], liga.nombre)
        if not candidatos:
            log.info(f"'{liga.nombre}': sin torneo de Sofascore parecido el {fecha} — sin anclar")
            continue

        for torneo_id, nombre_torneo in candidatos:
            if _intentar_match(db, partido, eventos_de(torneo_id, fecha), ya_usados):
                recordar_torneo(db, liga.id, torneo_id, nombre_torneo)
                break

    db.commit()


def correr_job_alineaciones():
    db = SessionLocal()
    try:
        a_anclar = _partidos_a_anclar(db)
        elegibles = _partidos_elegibles(db)
        if not a_anclar and not elegibles:
            log.info("Sin partidos por anclar ni por confirmar alineación")
            return

        from backend.pipeline.sofascore.cliente import SofascoreCliente
        from backend.pipeline.sofascore.parser import parsear_jugadores
        from backend.pipeline.sofascore.guardador_sofascore import guardar_jugadores

        log.info(f"{len(a_anclar)} partido(s) por anclar, {len(elegibles)} por confirmar alineación")
        with SofascoreCliente() as cliente:
            _anclar_sofascore_ids(db, cliente, a_anclar)

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
