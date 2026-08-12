"""Stats y jugadores EN VIVO desde Sofascore — xG, tiros, posesión,
corners, goles/tarjetas/atajadas por jugador, actualizados mientras el
partido se juega. /event/{id}/statistics y /event/{id}/lineups son los
MISMOS endpoints que ya usa el resto del pipeline (job_sofascore.py,
job_alineaciones.py) — Sofascore no tiene una variante "live" separada,
el endpoint normal YA devuelve el estado actual del partido en curso
(es literalmente lo que su propia web consulta mientras el usuario mira
un partido en vivo).

Sin costo de cuota de API-Football (Sofascore no comparte ese límite de
100 requests/día) — el límite acá es otro: no saturar de requests para
no gatillar el anti-bot de Sofascore (rate limit 429 ya manejado en
cliente.py con backoff de 60s, pero mejor no depender de eso).
Por eso:
  - Solo corre si hay partidos en vivo CON sofascore_id ya anclado (el
    mismo límite honesto que job_alineaciones.py — amistosos y ligas sin
    mapear en TEMPORADAS_HISTORICAS quedan afuera).
  - Un solo browser Chromium para toda la corrida (igual que el resto
    del pipeline), no uno por partido.
  - Se agenda cada 15 min — no cada pocos segundos. Es el mismo ritmo al
    que un hincha mirando el partido refresca la página a mano, no un
    patrón de scraping agresivo.
"""
import logging
from datetime import datetime, timezone
from backend.db.database import SessionLocal
from backend.db.modelos import Partido
from backend.pipeline.config import ahora_partidos
from backend.pipeline.job_partidos_en_vivo import _ESTADOS_EN_VIVO

log = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# status.type de Sofascore -> nuestro estado (códigos de API-Football,
# que es como quedó escrito el resto del sistema). "inprogress" no
# alcanza para saber el período, eso sale de status.description.
_TIPO_A_ESTADO = {
    "notstarted": "NS",
    "finished":   "FT",
    "postponed":  "PST",
    "canceled":   "CANC",
}


def _estado_desde_evento(evento: dict, estado_actual: str) -> str:
    status = evento.get("status") or {}
    tipo = status.get("type")
    if tipo in _TIPO_A_ESTADO:
        return _TIPO_A_ESTADO[tipo]
    if tipo != "inprogress":
        return estado_actual

    desc = (status.get("description") or "").lower()
    if "halftime" in desc or desc == "ht":
        return "HT"
    if "1st" in desc or "first" in desc:
        return "1H"
    if "2nd" in desc or "second" in desc:
        return "2H"
    if "extra" in desc or "overtime" in desc:
        return "ET"
    if "penalt" in desc:
        return "P"
    # En juego pero sin poder decir el período — no inventamos uno: si ya
    # veníamos con un código en vivo lo dejamos, si no marcamos 1H.
    return estado_actual if estado_actual in _ESTADOS_EN_VIVO else "1H"


def _goles_desde(marcador: dict):
    """Goles del TIEMPO REGLAMENTARIO.

    Ojo con "current": en un partido definido por penales trae el
    marcador de la tanda sumado (visto real: Arsenal vs Como terminó 1-1
    y "current" decía 5-4). "normaltime"/"display" son los buenos."""
    if not marcador:
        return None
    for clave in ("normaltime", "display", "current"):
        if marcador.get(clave) is not None:
            return marcador[clave]
    return None


def _minuto_desde_evento(evento: dict, estado: str):
    """Minuto en curso, derivado de cuándo arrancó el período actual —
    Sofascore no manda el minuto ya calculado (su web lo calcula igual
    que acá, en el cliente).

    ponytail: la fórmula no se pudo validar contra un partido EN CURSO
    (los dos que teníamos anclados ya habían terminado). Por eso es
    defensiva: si el número no da algo creíble devuelve None, y la UI
    cae a mostrar el período (1H/2H) sin minuto, que es lo que ya hacía
    cuando API-Football no mandaba 'elapsed'."""
    if estado not in ("1H", "2H", "ET"):
        return None
    inicio = (evento.get("time") or {}).get("currentPeriodStartTimestamp")
    if not inicio:
        return None
    offset = {"1H": 0, "2H": 45, "ET": 90}[estado]
    transcurrido = (datetime.now(timezone.utc).timestamp() - inicio) / 60
    if transcurrido < 0:
        return None
    # +1 por la convención del fútbol: apenas arranca se muestra 1', no
    # 0' (y el 2do tiempo arranca en 46', no en 45')
    minuto = int(transcurrido) + 1 + offset
    return minuto if 1 <= minuto <= 130 else None


def _partidos_hoy_anclados(db) -> list:
    """Todos los de hoy con sofascore_id — no solo los ya marcados en
    vivo: hace falta ver también los NS para enterarse de que
    arrancaron (antes de eso lo hacía job_partidos_en_vivo con
    API-Football, que se sacó para no gastar cuota)."""
    ahora = ahora_partidos()
    inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    from datetime import timedelta
    return (
        db.query(Partido)
        .filter(
            Partido.sofascore_id.isnot(None),
            Partido.fecha >= inicio,
            Partido.fecha < inicio + timedelta(days=1),
        )
        .all()
    )


def _partidos_en_vivo_anclados(db) -> list:
    return (
        db.query(Partido)
        .filter(Partido.estado.in_(_ESTADOS_EN_VIVO), Partido.sofascore_id.isnot(None))
        .all()
    )


def _partidos_a_refrescar(db, partidos_hoy: list) -> list:
    """Los que están EN VIVO, más los que YA TERMINARON hoy y todavía no
    tienen stats guardadas.

    Los terminados hacen falta porque el partido se acaba entre dos
    corridas del job: la última foto que alcanzamos a sacar es de unos
    minutos antes del pitido final, y nadie vuelve a buscar las
    definitivas hasta el job nocturno. Mientras tanto las predicciones
    de córners/tarjetas quedan pendientes aunque el partido terminó
    hace rato (bug real: PSG vs Aston Villa terminado, con "1X2" y
    "Goles" ya cerrados —esos salen del marcador— pero "Corners Over
    7.5" y "Tarjetas Over 1.5" pendientes, porque sin stats
    resolver_mercado no puede decidir)."""
    from backend.db.modelos import EstadisticaSofascore

    en_vivo = [p for p in partidos_hoy if p.estado in _ESTADOS_EN_VIVO and p.sofascore_id]

    con_stats = {
        fila.partido_id for fila in
        db.query(EstadisticaSofascore.partido_id)
        .filter(EstadisticaSofascore.partido_id.in_([p.id for p in partidos_hoy] or [0]))
        .all()
    }
    terminados_sin_stats = [
        p for p in partidos_hoy
        if p.estado == "FT" and p.sofascore_id and p.id not in con_stats
    ]

    ids_vivo = {p.id for p in en_vivo}
    return en_vivo + [p for p in terminados_sin_stats if p.id not in ids_vivo]


def _sincronizar_marcadores(db, cliente, partidos_hoy: list) -> int:
    """Actualiza estado/goles/minuto de los partidos de hoy desde
    Sofascore. Un request por torneo (trae TODOS sus partidos del día),
    no uno por partido.

    Esto lo hacía job_partidos_en_vivo.py con API-Football; se pasó acá
    para no gastar la cuota de 100/día en algo que Sofascore da gratis y
    dejarla entera para los jobs nocturnos (estadísticas y cuotas)."""
    from backend.pipeline.sofascore.cliente import LIGAS_SOFASCORE
    from backend.pipeline.sofascore.descubridor_torneos import torneos_conocidos
    from backend.db.modelos import Liga

    hoy = ahora_partidos().date()
    torneos = set()
    for partido in partidos_hoy:
        liga = db.get(Liga, partido.liga_id)
        if not liga:
            continue
        fijo = LIGAS_SOFASCORE.get(liga.nombre)
        if fijo:
            torneos.add(fijo)
        torneos.update(torneos_conocidos(db, liga.id))

    eventos_por_id = {}
    for torneo_id in torneos:
        for evento in cliente.get_partidos_liga_fecha(torneo_id, str(hoy)) or []:
            if evento.get("id"):
                eventos_por_id[evento["id"]] = evento

    actualizados = 0
    for partido in partidos_hoy:
        evento = eventos_por_id.get(partido.sofascore_id)
        if not evento:
            continue
        estado = _estado_desde_evento(evento, partido.estado)
        goles_l = _goles_desde(evento.get("homeScore"))
        goles_v = _goles_desde(evento.get("awayScore"))
        minuto = _minuto_desde_evento(evento, estado)

        if (estado, goles_l, goles_v, minuto) == (partido.estado, partido.goles_local,
                                                   partido.goles_visitante, partido.minuto):
            continue
        partido.estado = estado
        if goles_l is not None:
            partido.goles_local = goles_l
        if goles_v is not None:
            partido.goles_visitante = goles_v
        partido.minuto = minuto
        actualizados += 1

    db.commit()
    return actualizados


def correr_job_sofascore_en_vivo():
    db = SessionLocal()
    try:
        partidos_hoy = _partidos_hoy_anclados(db)
        if not partidos_hoy:
            log.info("Sin partidos de hoy con sofascore_id anclado — sin abrir browser")
            return

        from backend.pipeline.sofascore.cliente import SofascoreCliente
        from backend.pipeline.sofascore.parser import parsear_stats_partido, parsear_jugadores
        from backend.pipeline.sofascore.guardador_sofascore import guardar_stats_sofascore, guardar_jugadores

        stats_actualizadas = 0
        jugadores_actualizados = 0

        with SofascoreCliente() as cliente:
            actualizados = _sincronizar_marcadores(db, cliente, partidos_hoy)
            log.info(f"Marcador/estado actualizado en {actualizados} partido(s)")

            # se relee de la BD: _sincronizar_marcadores acaba de cambiar
            # estados, así que recién ahora se sabe quién está en vivo y
            # quién terminó
            db.expire_all()
            partidos_hoy = _partidos_hoy_anclados(db)
            objetivo = _partidos_a_refrescar(db, partidos_hoy)
            if objetivo:
                log.info(f"{len(objetivo)} partido(s) a refrescar (en vivo + terminados sin stats)")

            for partido in objetivo:
                stats_raw = cliente.get_stats_partido(partido.sofascore_id)
                if stats_raw:
                    stats = parsear_stats_partido(partido.id, partido.sofascore_id, stats_raw)
                    if stats:
                        guardar_stats_sofascore(db, stats)
                        stats_actualizadas += 1

                lineups_raw = cliente.get_lineups_partido(partido.sofascore_id)
                if lineups_raw:
                    jugadores = parsear_jugadores(
                        partido.id, lineups_raw,
                        partido.equipo_local_id, partido.equipo_visit_id)
                    if jugadores:
                        guardar_jugadores(db, jugadores, partido.id)
                        jugadores_actualizados += 1

        # Cerrar predicciones AL FINAL, ya con las stats guardadas — es
        # gratis (solo DB) y lo hacía job_partidos_en_vivo, que se sacó
        # del scheduler. El orden importa: los mercados de córners y
        # tarjetas necesitan las stats para resolverse; cerrando antes
        # de guardarlas quedaban pendientes hasta el job de las 01:30.
        if actualizados or stats_actualizadas:
            from backend.pipeline.job_cerrar_predicciones import correr_job_cerrar_predicciones
            correr_job_cerrar_predicciones()

        log.info(f"Stats de partido actualizadas: {stats_actualizadas} — planteles actualizados: {jugadores_actualizados}")
    finally:
        db.close()


if __name__ == "__main__":
    correr_job_sofascore_en_vivo()
