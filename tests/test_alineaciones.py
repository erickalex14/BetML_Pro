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
    assert not _nombre_coincide("Arsenal", "Chelsea")
    assert not _nombre_coincide("", "Arsenal")


def test_abreviaturas_pasan_por_la_regla_de_ventaja():
    """Abreviaturas y renombres puntúan por debajo del umbral estricto —
    se aceptan solo cuando son el candidato claramente mejor del torneo
    y la fecha (ver _intentar_match). Casos reales del 2026-08-12: por
    no contemplarlos, los partidos de Sudamericana se quedaban sin
    anclar y por lo tanto sin marcador en vivo.

    (Este test nació de un error propio: el anterior daba por sentado
    que "Atletico-MG" y "Atletico Mineiro" eran equipos distintos.)"""
    from backend.pipeline.sofascore.job_alineaciones import (
        _similitud, UMBRAL_CON_VENTAJA, UMBRAL_SIMILITUD)

    for a, b in [("RB Bragantino", "Red Bull Bragantino"),
                 ("Atletico-MG", "Atlético Mineiro"),
                 ("Atletico Torque", "Montevideo City Torque"),
                 ("Rapid Vienna", "SK Rapid Wien"),
                 ("FC Copenhagen", "FC København")]:
        assert _similitud(a, b) >= UMBRAL_CON_VENTAJA, f"{a} / {b}"

    # y los distintos siguen por debajo de ese piso mas permisivo
    assert _similitud("Arsenal", "Chelsea") < UMBRAL_CON_VENTAJA
    assert _similitud("Boca Juniors", "River Plate") < UMBRAL_CON_VENTAJA
    # ojo: estos SI puntuan alto, por eso hace falta la ventaja sobre el
    # segundo candidato ademas del puntaje
    assert _similitud("Independiente", "Independiente del Valle") >= UMBRAL_SIMILITUD


def test_match_debil_exige_al_menos_un_equipo_fuerte():
    from backend.pipeline.sofascore.job_alineaciones import _aceptar_match

    # Caso real falso: Platense-Boca fue asociado a River-Argentinos.
    assert not _aceptar_match(mejor=0.53, segundo=0.20,
                              lado_mas_fuerte=0.60)
    # Caso legítimo: un nombre exacto y su rival renombrado/abreviado.
    assert _aceptar_match(mejor=0.53, segundo=0.20,
                          lado_mas_fuerte=1.0)
    assert _aceptar_match(mejor=0.90, segundo=0.89,
                          lado_mas_fuerte=0.95)


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


def test_ventana_de_anclaje_cubre_los_dos_dias_de_cuotas():
    from datetime import timedelta
    from backend.pipeline.config import ahora_partidos
    from backend.pipeline.sofascore.job_alineaciones import _partidos_a_anclar

    db = SessionLocal()
    partido_id = 99881
    equipo_ids = (81881, 81882)
    try:
        db.query(Partido).filter(Partido.id == partido_id).delete()
        _equipo_temporal(db, equipo_ids[0], "Ventana local")
        _equipo_temporal(db, equipo_ids[1], "Ventana visitante")
        db.add(Partido(
            id=partido_id, liga_id=39, temporada=2026,
            equipo_local_id=equipo_ids[0], equipo_visit_id=equipo_ids[1],
            fecha=ahora_partidos() + timedelta(days=2), estado="NS",
        ))
        db.commit()

        assert partido_id not in {p.id for p in _partidos_a_anclar(db)}
        assert partido_id in {p.id for p in _partidos_a_anclar(db, 2)}
    finally:
        db.query(Partido).filter(Partido.id == partido_id).delete()
        db.commit()
        db.close()
