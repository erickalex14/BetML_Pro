from backend.db.database import SessionLocal
from backend.db.modelos import EstadisticaJugador, Partido
from backend.models.jugadores_montecarlo import mercados_jugadores_calculados
from backend.models.resolver_mercado import resolver_mercado


def test_aplana_mercado_jugador_con_clave_estable():
    resultado = {"local": [{
        "sofascore_jugador_id": 123,
        "nombre": "Delantero Test",
        "posicion": "F",
        "n_partidos_historial": 5,
        "tiros": {"over_under": {"over_1_5": 0.64}},
        "tiros_arco": {"over_under": {}},
        "goles": {"over_under": {}},
        "asistencias": {"over_under": {}},
        "pases": {"over_under": {}},
        "entradas": {"over_under": {}},
        "atajadas": {"over_under": {"over_1_5": 0.7}},
    }], "visitante": []}

    mercados = mercados_jugadores_calculados(resultado)

    assert [m["clave"] for m in mercados] == ["jugador_123_tiros_over_1_5"]
    assert mercados[0]["probabilidad"] == 0.64
    assert mercados[0]["requiere_cuota"] is True


def test_resuelve_mercado_jugador_con_stat_real():
    db = SessionLocal()
    partido = db.query(Partido).filter(Partido.estado == "FT").first()
    jugador_id = 987654321
    db.query(EstadisticaJugador).filter(
        EstadisticaJugador.partido_id == partido.id,
        EstadisticaJugador.sofascore_jugador_id == jugador_id,
    ).delete()
    db.add(EstadisticaJugador(
        partido_id=partido.id,
        equipo_id=partido.equipo_local_id,
        sofascore_jugador_id=jugador_id,
        nombre="Jugador cierre",
        es_local=True,
        tiros=2,
    ))
    db.commit()
    try:
        assert resolver_mercado(
            db, partido, f"jugador_{jugador_id}_tiros_over_1_5") is True
        assert resolver_mercado(
            db, partido, f"jugador_{jugador_id}_tiros_over_2_5") is False
    finally:
        db.query(EstadisticaJugador).filter(
            EstadisticaJugador.partido_id == partido.id,
            EstadisticaJugador.sofascore_jugador_id == jugador_id,
        ).delete()
        db.commit()
        db.close()
