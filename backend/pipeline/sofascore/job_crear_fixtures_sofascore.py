"""Crea Partido/Equipo desde Sofascore para temporadas que API-Football
no puede traer (25/26+, bloqueado en el plan free — solo permite 2022-2024).

A diferencia de job_historico_sofascore.py, que solo ADJUNTA stats a
partidos ya existentes, este job CREA las filas de Partido/Equipo desde
cero usando a Sofascore como fuente de fixtures.

Antes de crear, siempre intenta encontrar el partido vía el mismo matcher
que usa job_historico_sofascore.py (_buscar_partido): algunas de estas
temporadas SÍ se solapan con datos ya cargados por API-Football (Liga MX
agrupa Apertura+Clausura bajo un único "temporada", así que
"Clausura 2025" puede ya existir dentro del bucket temporada=2024). Crear
a ciegas duplicaría esos partidos.
"""
import logging
from datetime import datetime
from backend.db.database import SessionLocal, crear_tablas
from backend.db.modelos import Partido, Equipo
from backend.pipeline.sofascore.cliente import SofascoreCliente
from backend.pipeline.sofascore.equipos import (
    resolver_liga_id,
    buscar_candidatos,
    UMBRAL_ANCLAJE,
)
from backend.pipeline.sofascore.job_historico_sofascore import _buscar_partido

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)


def correr_job_crear_fixtures_sofascore(entradas: list):
    """entradas: lista (nombre_liga, sofascore_liga_id, season_id, label),
    mismo formato que TEMPORADAS_HISTORICAS — pasar solo las temporadas
    que hace falta crear (25/26+), no toda la lista."""
    log.info("=" * 55)
    log.info("  Crear fixtures desde Sofascore")
    log.info("=" * 55)

    crear_tablas()
    db = SessionLocal()
    creados = 0
    ya_existian = 0
    ambiguos = 0

    try:
        with SofascoreCliente(headless=True) as cliente:
            for nombre_liga, liga_id, season_id, label in entradas:
                db_liga_id = resolver_liga_id(db, nombre_liga)
                if not db_liga_id:
                    log.warning(f"Liga '{nombre_liga}' no existe en BD — salteando")
                    continue

                log.info(f"\n>>> {nombre_liga} — {label} (season: {season_id})")
                temporada = _parsear_temporada(label)

                pagina = 0
                while True:
                    eventos = cliente.get_partidos_liga_temporada(
                        liga_id=liga_id, temporada_id=season_id, pagina=pagina
                    )
                    if not eventos:
                        break
                    log.info(f"  Página {pagina}: {len(eventos)} partidos")

                    for evento in eventos:
                        if evento.get("status", {}).get("type") != "finished":
                            continue
                        sofascore_id = evento.get("id")
                        if not sofascore_id:
                            continue

                        # Ya guardado en una corrida anterior de este job
                        if db.query(Partido).filter(Partido.sofascore_id == sofascore_id).first():
                            ya_existian += 1
                            continue

                        # Puede que ya exista vía API-Football (solapamiento
                        # de temporadas) — si lo encuentra, solo ancla el
                        # sofascore_id, no duplica.
                        existente = _buscar_partido(db, evento, db_liga_id)
                        if existente:
                            existente.sofascore_id = sofascore_id
                            db.commit()
                            ya_existian += 1
                            continue

                        home = evento.get("homeTeam", {})
                        away = evento.get("awayTeam", {})
                        equipo_local = _resolver_o_crear_equipo(
                            db, home.get("name", ""), home.get("id"), db_liga_id)
                        equipo_visit = _resolver_o_crear_equipo(
                            db, away.get("name", ""), away.get("id"), db_liga_id)

                        if not equipo_local or not equipo_visit:
                            log.warning(
                                f"  Empate ambiguo de nombre sin partido de referencia — "
                                f"salteando {home.get('name')} vs {away.get('name')}")
                            ambiguos += 1
                            continue

                        hs = evento.get("homeScore", {})
                        as_ = evento.get("awayScore", {})
                        partido = Partido(
                            liga_id=db_liga_id,
                            equipo_local_id=equipo_local.id,
                            equipo_visit_id=equipo_visit.id,
                            fecha=datetime.fromtimestamp(evento.get("startTimestamp", 0)),
                            estado="FT",
                            goles_local=hs.get("current"),
                            goles_visitante=as_.get("current"),
                            goles_local_ht=hs.get("period1"),
                            goles_visit_ht=as_.get("period1"),
                            temporada=temporada,
                            jornada=str(evento.get("roundInfo", {}).get("round", "")),
                            sofascore_id=sofascore_id,
                        )
                        db.add(partido)
                        db.commit()
                        creados += 1
                        log.info(
                            f"  Creado: {home.get('name')} vs {away.get('name')} "
                            f"({partido.fecha.date()})")

                    if len(eventos) < 30:
                        break
                    pagina += 1

    except Exception as e:
        log.error(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        log.info("\n" + "=" * 55)
        log.info(f"  Partidos creados      : {creados}")
        log.info(f"  Ya existían (ancorado): {ya_existian}")
        log.info(f"  Empates ambiguos      : {ambiguos}")
        log.info("=" * 55)


def _resolver_o_crear_equipo(db, nombre: str, sofascore_team_id, liga_id: int) -> Equipo | None:
    candidatos = buscar_candidatos(db, nombre, sofascore_team_id, liga_id)

    if candidatos:
        # Empate real entre 2+ candidatos y sin partido de referencia para
        # desambiguar (a diferencia de _buscar_partido, acá no hay fecha+
        # rival confirmados aún) — no se puede crear de forma segura.
        if len(candidatos) > 1 and candidatos[0][1] is not None and candidatos[0][1] == candidatos[1][1]:
            return None

        equipo, score = candidatos[0]
        if sofascore_team_id and not equipo.sofascore_id and (score is None or score >= UMBRAL_ANCLAJE):
            equipo.sofascore_id = sofascore_team_id
            db.commit()
        return equipo

    # Equipo genuinamente nuevo (recién ascendido, etc.) — id lo asigna
    # Postgres por secuencia, no el id de Sofascore (ese va en sofascore_id;
    # usarlo como PK arriesgaría chocar con ids ya usados por API-Football).
    equipo = Equipo(nombre=nombre, sofascore_id=sofascore_team_id)
    db.add(equipo)
    db.commit()
    return equipo


def _parsear_temporada(label: str) -> int:
    """"25/26" -> 2025 | "2025" -> 2025 | "Apertura 2025" -> 2025 |
    "Clausura 2026" -> 2025 (sigue la convención ya usada en BD: Clausura
    de año N+1 pertenece a la temporada N, agrupada con la Apertura N)."""
    import re
    es_clausura = label.strip().lower().startswith("clausura")
    anios = re.findall(r"\d{4}", label)
    if anios:
        anio = int(anios[0])
        return anio - 1 if es_clausura else anio
    m = re.match(r"(\d{2})/(\d{2})", label)
    if m:
        return 2000 + int(m.group(1))
    raise ValueError(f"No se pudo parsear temporada de label: {label!r}")


def _es_temporada_2025_en_adelante(label: str) -> bool:
    import re
    m = re.match(r"(\d{2})/(\d{2})", label)
    if m:
        return int(m.group(1)) >= 25
    anios = re.findall(r"\d{4}", label)
    return bool(anios) and int(anios[0]) >= 2025


if __name__ == "__main__":
    from backend.pipeline.sofascore.cliente import TEMPORADAS_HISTORICAS
    entradas_2526 = [
        t for t in TEMPORADAS_HISTORICAS if _es_temporada_2025_en_adelante(t[3])
    ]
    correr_job_crear_fixtures_sofascore(entradas_2526)
