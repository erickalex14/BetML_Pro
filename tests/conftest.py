"""Aísla la suite de la base de PRODUCCIÓN.

El `.env` de desarrollo apunta a la base del server por el túnel SSH, así
que hasta ahora `pytest` insertaba usuarios, partidos y predicciones
reales (pasó: quedaron `beta@gmail.com` y `aislamiento@gmail.com` en
prod). Este archivo se importa antes que cualquier test, así que acá se
redirige `SessionLocal` a una base de pruebas ANTES de que los módulos
de test la usen.

Cómo funciona:
  - `BETML_TEST_DB_URL` es obligatoria. Las tablas van a un **schema aparte**
    (`BETML_TEST_SCHEMA`, por default `betml_test`) y no a `public`:
    el usuario local no tiene permiso de `create database`, pero sí de
    `create schema`, y el aislamiento es el mismo.
  - Si esa URL apunta al mismo servidor/base que `DB_URL`, la suite
    **aborta**: es exactamente el accidente que este archivo evita.
  - `SessionLocal.configure(bind=...)` muta el sessionmaker en su lugar,
    así que los 8 archivos que hacen `from backend.db.database import
    SessionLocal` quedan redirigidos sin tocarlos — y también el código
    bajo test que abre su propia sesión (`correr_job_cerrar_predicciones`).

Postgres es la opción recomendada: hay SQL crudo con sintaxis propia.
"""
import os
from datetime import date, datetime, time, timedelta

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

import backend.db.database as database
from backend.pipeline.config import DB_URL

TEST_DB_URL = os.getenv("BETML_TEST_DB_URL")
TEST_SCHEMA = os.getenv("BETML_TEST_SCHEMA", "betml_test")

if not TEST_DB_URL:
    pytest.exit(
        "BETML_TEST_DB_URL no está definida. La suite no arrancará porque "
        "DB_URL apunta a la base usada por la aplicación.",
        returncode=1,
    )


def _destino(url: str) -> tuple:
    u = make_url(url)
    # localhost y 127.0.0.1 son el mismo server: sin normalizar, el
    # chequeo de abajo se lo comería.
    host = "127.0.0.1" if u.host in ("localhost", "::1") else u.host
    return (host, u.port, u.database)


if _destino(TEST_DB_URL) == _destino(DB_URL):
    pytest.exit(
        "La base de tests apunta al MISMO destino que DB_URL "
        f"({_destino(DB_URL)}). Si eso es producción, la suite la "
        "ensucia. Definí BETML_TEST_DB_URL a una base aparte.",
        returncode=1,
    )


def _crear_schema_si_falta(url: str, schema: str) -> None:
    """`create_all` crea tablas, no el schema que las contiene."""
    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as con:
            con.execute(text(f'create schema if not exists "{schema}"'))
    finally:
        admin.dispose()


_es_postgres = make_url(TEST_DB_URL).get_backend_name() == "postgresql"
if _es_postgres:
    _crear_schema_si_falta(TEST_DB_URL, TEST_SCHEMA)

_engine_test = create_engine(
    TEST_DB_URL,
    pool_pre_ping=True,
    # Sin `public` en el search_path: si el schema de test no tiene una
    # tabla, tiene que fallar ruidoso y no leer la de desarrollo.
    connect_args={"options": f"-csearch_path={TEST_SCHEMA}"} if _es_postgres else {},
)
database.engine = _engine_test          # lo lee crear_tablas()
database.SessionLocal.configure(bind=_engine_test)
database.crear_tablas()


# ── Semilla ───────────────────────────────────────────────────────────
# Varios tests fueron escritos contra los datos reales de prod: piden el
# partido FT número 500 y 700 por fecha, un partido de hoy, y el id fijo
# 1547761. En vez de reescribir los 8 archivos, la base de test arranca
# con datos sintéticos que cumplen esas formas.

N_PARTIDOS_FT = 800          # test_mlops pide offset(700).limit(2)
PARTIDO_FIJO = 1547761       # hardcodeado en test_predicciones_por_usuario
IDS_EQUIPOS_HISTORICOS = range(1, 25)
IDS_EQUIPOS_HOY = range(90, 96)   # separados a propósito de los históricos:
# test_parser_imagen exige que el par de equipos del partido VIEJO no
# tenga ningún partido reciente, si no el chequeo de ventana no se dispara.


def _sembrar() -> None:
    from backend.db.modelos import Equipo, Liga, Partido

    db = database.SessionLocal()
    try:
        if db.query(Partido).count() >= N_PARTIDOS_FT:
            return

        for lid, nombre in [(39, "Premier League"), (140, "La Liga"),
                            (667, "Friendlies Clubs")]:
            if db.get(Liga, lid) is None:
                db.add(Liga(id=lid, nombre=nombre, pais="Test", temporada=2025))

        for eid in list(IDS_EQUIPOS_HISTORICOS) + list(IDS_EQUIPOS_HOY):
            if db.get(Equipo, eid) is None:
                db.add(Equipo(id=eid, nombre=f"Equipo Semilla {eid}", pais="Test"))
        db.commit()

        base = datetime(2023, 1, 1, 15, 0)
        for i in range(N_PARTIDOS_FT):
            pid = 1000 + i
            if db.get(Partido, pid) is not None:
                continue
            db.add(Partido(
                id=pid, liga_id=39, temporada=2025,
                equipo_local_id=1 + (i % 12),
                equipo_visit_id=13 + ((i + i // 12) % 12),
                fecha=base + timedelta(days=i),
                estado="FT",
                goles_local=i % 4,
                goles_visitante=(i // 3) % 4,
            ))

        if db.get(Partido, PARTIDO_FIJO) is None:
            db.add(Partido(
                id=PARTIDO_FIJO, liga_id=39, temporada=2025,
                equipo_local_id=1, equipo_visit_id=13,
                fecha=base, estado="FT", goles_local=1, goles_visitante=0,
            ))

        # Partidos de hoy: los necesitan get_partidos_hoy() y el test de
        # desambiguación, que busca el partido más cercano a ahora.
        hoy = datetime.combine(date.today(), time(15, 0))
        for n, (local, visita) in enumerate([(90, 91), (92, 93), (94, 95)]):
            pid = 900001 + n
            if db.get(Partido, pid) is not None:
                continue
            db.add(Partido(
                id=pid, liga_id=39, temporada=2025,
                equipo_local_id=local, equipo_visit_id=visita,
                fecha=hoy + timedelta(hours=n), estado="NS",
            ))

        db.commit()
    finally:
        db.close()


_sembrar()
