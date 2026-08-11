"""Tests del tracking MLOps — sin esto, las predicciones se guardan y
jamás se comparan con el resultado real (bug real encontrado en sesión:
marcar_resultado() existía pero nadie lo llamaba)."""
import pytest
from backend.db.database import SessionLocal
from backend.db.modelos import Partido, Prediccion
from backend.repositories.prediccion_repo import PrediccionRepository
from backend.pipeline.job_cerrar_predicciones import correr_job_cerrar_predicciones
from backend.models.ensemble import _peso_modelo, MIN_MUESTRAS_PESO


@pytest.fixture
def partido_ft():
    """Un partido FT real de la BD, con su Prediccion de prueba limpiada
    antes y después."""
    db = SessionLocal()
    p = (db.query(Partido)
         .filter(Partido.estado == "FT", Partido.goles_local.isnot(None))
         .order_by(Partido.fecha.asc()).offset(500).first())
    db.query(Prediccion).filter(Prediccion.partido_id == p.id).delete()
    db.commit()
    yield db, p
    db.query(Prediccion).filter(Prediccion.partido_id == p.id).delete()
    db.commit()
    db.close()


def test_job_cierra_prediccion_pendiente_con_resultado_real(partido_ft):
    db, partido = partido_ft
    repo = PrediccionRepository(db)

    # mercado="1X2" con prediccion="Local"/"Empate"/"Visitante" es el
    # único formato que _clave_mercado() sabe traducir a la clave interna
    # de resolver_mercado.py (mercados random no se resuelven a ciegas)
    repo.crear(partido_id=partido.id, mercado="1X2", prediccion="Local",
               probabilidad=0.5, confianza=0.5)

    fila = db.query(Prediccion).filter(Prediccion.partido_id == partido.id).first()
    assert fila.acerto is None  # recién creada, sin cerrar

    correr_job_cerrar_predicciones()

    db.refresh(fila)
    resultado_esperado = (
        "Local" if partido.goles_local > partido.goles_visitante
        else "Empate" if partido.goles_local == partido.goles_visitante
        else "Visitante"
    )
    assert fila.resultado_real == resultado_esperado
    assert fila.acerto == (fila.prediccion == resultado_esperado)


def test_job_cierra_variante_1x2_por_modelo(partido_ft):
    """mercado="1X2-xgboost" (predicción individual del ensemble, no el
    combinado) tiene que cerrar igual que "1X2" — _clave_mercado() ahora
    usa startswith("1X2") en vez de comparar contra 2 strings fijas."""
    db, partido = partido_ft
    repo = PrediccionRepository(db)
    repo.crear(partido_id=partido.id, mercado="1X2-xgboost", prediccion="Local",
               probabilidad=0.5, confianza=0.5)

    correr_job_cerrar_predicciones()

    fila = db.query(Prediccion).filter(Prediccion.partido_id == partido.id).first()
    resultado_esperado = (
        "Local" if partido.goles_local > partido.goles_visitante
        else "Empate" if partido.goles_local == partido.goles_visitante
        else "Visitante"
    )
    assert fila.resultado_real == resultado_esperado
    assert fila.acerto == (fila.prediccion == resultado_esperado)


def test_job_cierra_mercado_no_1x2(partido_ft):
    """goles_over_X_X, corners_over_X_X, etc — la parte nueva de esta
    sesión: antes SOLO se trackeaba 1X2, cualquier otro mercado se
    quedaba sin cerrar para siempre."""
    db, partido = partido_ft
    repo = PrediccionRepository(db)

    goles_total = partido.goles_local + partido.goles_visitante
    mercado = f"goles_over_{goles_total - 1}_5"  # linea que sabemos que gano

    repo.crear(partido_id=partido.id, mercado=mercado, prediccion="Over",
               probabilidad=0.5, confianza=0.5)

    correr_job_cerrar_predicciones()

    fila = db.query(Prediccion).filter(Prediccion.partido_id == partido.id).first()
    assert fila.acerto is True
    assert fila.resultado_real == "Ganó"


def test_stats_por_mercado_no_mezcla_fuentes(partido_ft):
    db, partido = partido_ft
    repo = PrediccionRepository(db)
    repo.crear(partido_id=partido.id, mercado="test-mercado-unico",
               prediccion="Local", probabilidad=0.5, confianza=0.5)

    stats = repo.get_stats()
    assert "test-mercado-unico" in stats["por_mercado"]
    assert stats["por_mercado"]["test-mercado-unico"]["total"] >= 1


@pytest.fixture
def historial_modelo():
    """Filas Prediccion de un modelo ficticio, ya cerradas — para probar
    _peso_modelo() sin depender de que el ensemble real haya corrido."""
    db = SessionLocal()
    partido = (db.query(Partido)
               .filter(Partido.estado == "FT", Partido.goles_local.isnot(None))
               .order_by(Partido.fecha.asc()).offset(500).first())
    mercado = "1X2-modelo_test_peso"
    db.query(Prediccion).filter(Prediccion.mercado == mercado).delete()
    db.commit()
    yield db, partido, mercado
    db.query(Prediccion).filter(Prediccion.mercado == mercado).delete()
    db.commit()
    db.close()


def _crear_cerradas(db, partido, mercado, n_aciertos, n_fallos):
    for _ in range(n_aciertos):
        db.add(Prediccion(partido_id=partido.id, mercado=mercado, prediccion="Local",
                           probabilidad=0.5, confianza=0.5, resultado_real="Local", acerto=True))
    for _ in range(n_fallos):
        db.add(Prediccion(partido_id=partido.id, mercado=mercado, prediccion="Local",
                           probabilidad=0.5, confianza=0.5, resultado_real="Visitante", acerto=False))
    db.commit()


def test_peso_modelo_usa_fallback_con_pocas_muestras(historial_modelo):
    db, partido, mercado = historial_modelo
    _crear_cerradas(db, partido, mercado, n_aciertos=5, n_fallos=5)  # 10 < MIN_MUESTRAS_PESO

    peso = _peso_modelo(db, "modelo_test_peso", val_acc_fallback=0.777)
    assert peso == 0.777


def test_peso_modelo_usa_accuracy_real_con_historial_suficiente(historial_modelo):
    db, partido, mercado = historial_modelo
    n = MIN_MUESTRAS_PESO
    _crear_cerradas(db, partido, mercado, n_aciertos=n, n_fallos=0)  # 100% real, != fallback

    peso = _peso_modelo(db, "modelo_test_peso", val_acc_fallback=0.5)
    assert peso == 1.0


@pytest.fixture
def dos_partidos_ft():
    db = SessionLocal()
    partidos = (db.query(Partido)
                .filter(Partido.estado == "FT", Partido.goles_local.isnot(None))
                .order_by(Partido.fecha.asc()).offset(700).limit(2).all())
    yield db, partidos
    from backend.db.modelos import Parlay, ParlaySeleccion
    ids_partidos = [p.id for p in partidos]
    parlay_ids = [p.id for p in db.query(Parlay.id)
                  .join(ParlaySeleccion, ParlaySeleccion.parlay_id == Parlay.id)
                  .filter(ParlaySeleccion.partido_id.in_(ids_partidos)).all()]
    db.query(ParlaySeleccion).filter(ParlaySeleccion.parlay_id.in_(parlay_ids)).delete(synchronize_session=False)
    db.query(Parlay).filter(Parlay.id.in_(parlay_ids)).delete(synchronize_session=False)
    db.commit()
    db.close()


def test_parlay_se_cierra_solo_cuando_todas_las_patas_resuelven(dos_partidos_ft):
    from backend.db.modelos import Parlay, ParlaySeleccion

    db, (p1, p2) = dos_partidos_ft
    res1 = "local" if p1.goles_local > p1.goles_visitante else (
        "empate" if p1.goles_local == p1.goles_visitante else "visitante")
    res2 = "local" if p2.goles_local > p2.goles_visitante else (
        "empate" if p2.goles_local == p2.goles_visitante else "visitante")

    parlay = Parlay(cuota_combinada=4.0, prob_combinada=0.25, stake_pct=1.0, bankroll=1000)
    db.add(parlay)
    db.flush()
    db.add(ParlaySeleccion(parlay_id=parlay.id, partido_id=p1.id, mercado=res1,
                            nombre="p1", probabilidad=0.5, cuota=2.0))
    db.add(ParlaySeleccion(parlay_id=parlay.id, partido_id=p2.id, mercado=res2,
                            nombre="p2", probabilidad=0.5, cuota=2.0))
    db.commit()
    parlay_id = parlay.id

    assert parlay.acerto is None

    correr_job_cerrar_predicciones()

    db.refresh(parlay)
    assert parlay.acerto is True  # ambas patas eran el resultado real -> parlay entero gano
