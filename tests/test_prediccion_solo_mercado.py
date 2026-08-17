from backend.db.database import SessionLocal
from backend.db.modelos import Odds, Partido
from backend.models.odds_service import probabilidades_mercado_1x2
from backend.services.prediccion_service import PrediccionService
from backend.pipeline.odds.orquestador import partidos_sin_cuotas


PARTIDO_ID = 900001
CASAS_TEST = ("CasaCompleta", "CasaIncompleta")


def _limpiar(db):
    db.query(Odds).filter(
        Odds.partido_id == PARTIDO_ID,
        Odds.bookmaker.in_(CASAS_TEST),
    ).delete(synchronize_session=False)
    db.commit()


def test_fallback_usa_una_misma_casa_y_no_inventa_edge():
    db = SessionLocal()
    try:
        _limpiar(db)
        db.add_all([
            Odds(partido_id=PARTIDO_ID, bookmaker="CasaCompleta", mercado="odds_local", valor=2.0),
            Odds(partido_id=PARTIDO_ID, bookmaker="CasaCompleta", mercado="odds_empate", valor=3.5),
            Odds(partido_id=PARTIDO_ID, bookmaker="CasaCompleta", mercado="odds_visitante", valor=4.0),
            # La mejor cuota aislada no puede mezclarse con otra casa.
            Odds(partido_id=PARTIDO_ID, bookmaker="CasaIncompleta", mercado="odds_local", valor=9.0),
        ])
        db.commit()

        probs = probabilidades_mercado_1x2(db, PARTIDO_ID)
        pred = PrediccionService(db).predecir(db.get(Partido, PARTIDO_ID))

        assert probs is not None
        assert probs["bookmaker_referencia"] == "CasaCompleta"
        assert round(probs["prob_local"] + probs["prob_empate"] + probs["prob_visitante"], 3) == 1.0
        assert pred is not None
        assert pred["origen_prediccion"] == "mercado"
        assert pred["calidad_datos"] == "solo_mercado"
    finally:
        _limpiar(db)
        db.close()


def test_fallback_exige_mercado_1x2_completo():
    db = SessionLocal()
    try:
        _limpiar(db)
        db.add(Odds(
            partido_id=PARTIDO_ID,
            bookmaker="CasaIncompleta",
            mercado="odds_local",
            valor=2.0,
        ))
        db.commit()

        assert probabilidades_mercado_1x2(db, PARTIDO_ID) is None
    finally:
        _limpiar(db)
        db.close()


def test_cascada_no_considera_cubierto_un_partido_con_cuotas_parciales():
    db = SessionLocal()
    partido_id = 900002
    casa = "CasaCascada"
    try:
        db.query(Odds).filter(Odds.partido_id == partido_id,
                              Odds.bookmaker == casa).delete()
        db.add(Odds(partido_id=partido_id, bookmaker=casa,
                    mercado="odds_local", valor=2.0))
        db.commit()
        assert partido_id in {p.id for p in partidos_sin_cuotas(db)}

        db.add_all([
            Odds(partido_id=partido_id, bookmaker=casa,
                 mercado="odds_empate", valor=3.2),
            Odds(partido_id=partido_id, bookmaker=casa,
                 mercado="odds_visitante", valor=4.0),
        ])
        db.commit()
        assert partido_id not in {p.id for p in partidos_sin_cuotas(db)}
    finally:
        db.query(Odds).filter(Odds.partido_id == partido_id,
                              Odds.bookmaker == casa).delete()
        db.commit()
        db.close()
