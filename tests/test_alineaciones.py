"""Bug real encontrado en sesión: Endrick (ya no juega en Lyon) seguía
apareciendo como titular probable de Lyon, porque el heurístico cuenta
titularidades en partidos VIEJOS sin saber de transferencias. Estos tests
cubren el fix: 1) guardar_jugadores ahora actualiza en vez de saltarse
si ya hay filas (el bug que habría bloqueado los stats reales post-
partido si se guarda la alineación confirmada antes), 2) la alineación
confirmada gana sobre el heurístico cuando existe."""
from backend.db.database import SessionLocal
from backend.db.modelos import Partido, Equipo, EstadisticaJugador
from backend.pipeline.sofascore.guardador_sofascore import guardar_jugadores
from backend.features.jugadores import obtener_lineup_confirmada


def _equipo_temporal(db, id_, nombre):
    if db.get(Equipo, id_) is None:
        db.add(Equipo(id=id_, nombre=nombre))
        db.commit()


def _partido_temporal(db):
    _equipo_temporal(db, 950001, "Equipo Alineacion A")
    _equipo_temporal(db, 950002, "Equipo Alineacion B")
    from datetime import datetime
    p = Partido(id=950000, liga_id=39, temporada=2025,
                equipo_local_id=950001, equipo_visit_id=950002,
                fecha=datetime.utcnow(), estado="NS")
    db.merge(p)
    db.commit()
    return p.id


def _limpiar(db):
    db.query(EstadisticaJugador).filter(EstadisticaJugador.partido_id == 950000).delete()
    db.query(Partido).filter(Partido.id == 950000).delete()
    db.commit()


def test_nombre_coincide_tolera_guiones_acentos_y_palabras_extra():
    """Casos REALES que quedaban sin anclar el 2026-08-12 — las dos
    fuentes escriben el mismo club distinto, y sin sofascore_id el
    partido se queda sin alineación confirmada NI stats en vivo."""
    from backend.pipeline.sofascore.job_alineaciones import _nombre_coincide

    # guiones y acentos
    assert _nombre_coincide("Paris Saint Germain", "Paris Saint-Germain")
    assert _nombre_coincide("Bolivar", "Bolívar")
    # palabras/números extra en el medio (lo que rompía el substring)
    assert _nombre_coincide("Bayer Leverkusen", "Bayer 04 Leverkusen")
    assert _nombre_coincide("Deportivo La Coruna", "Deportivo de A Coruña")
    assert _nombre_coincide("Aston Villa", "Aston Villa")
    # equipos distintos de verdad NO deben matchear
    assert not _nombre_coincide("Atletico-MG", "Atlético Mineiro")
    assert not _nombre_coincide("Arsenal", "Chelsea")
    assert not _nombre_coincide("Real Madrid", "Real Sociedad")
    assert not _nombre_coincide("", "Arsenal")


def test_guardar_jugadores_actualiza_en_vez_de_saltar_si_ya_existe():
    db = SessionLocal()
    try:
        partido_id = _partido_temporal(db)

        pre_partido = EstadisticaJugador(
            partido_id=partido_id, equipo_id=950001, sofascore_jugador_id=1,
            nombre="Jugador Test", es_local=True, titular=True, goles=None)
        assert guardar_jugadores(db, [pre_partido], partido_id) == 1

        post_partido = EstadisticaJugador(
            partido_id=partido_id, equipo_id=950001, sofascore_jugador_id=1,
            nombre="Jugador Test", es_local=True, titular=True, goles=2)
        guardar_jugadores(db, [post_partido], partido_id)

        fila = (db.query(EstadisticaJugador)
                .filter(EstadisticaJugador.partido_id == partido_id,
                        EstadisticaJugador.sofascore_jugador_id == 1).one())
        assert fila.goles == 2  # antes del fix se quedaba en None para siempre
    finally:
        _limpiar(db)
        db.close()


def test_lineup_confirmada_devuelve_solo_titulares_del_lado_correcto():
    db = SessionLocal()
    try:
        partido_id = _partido_temporal(db)
        db.add(EstadisticaJugador(partido_id=partido_id, equipo_id=950001,
                                   sofascore_jugador_id=10, nombre="Titular Local",
                                   es_local=True, titular=True))
        db.add(EstadisticaJugador(partido_id=partido_id, equipo_id=950001,
                                   sofascore_jugador_id=11, nombre="Suplente Local",
                                   es_local=True, titular=False))
        db.add(EstadisticaJugador(partido_id=partido_id, equipo_id=950002,
                                   sofascore_jugador_id=20, nombre="Titular Visita",
                                   es_local=False, titular=True))
        db.commit()

        locales = obtener_lineup_confirmada(db, partido_id, es_local=True)
        assert len(locales) == 1
        assert locales[0]["nombre"] == "Titular Local"
    finally:
        _limpiar(db)
        db.close()


def test_lineup_confirmada_vacia_si_todavia_no_se_publico():
    db = SessionLocal()
    try:
        partido_id = _partido_temporal(db)
        assert obtener_lineup_confirmada(db, partido_id, es_local=True) == []
    finally:
        _limpiar(db)
        db.close()
