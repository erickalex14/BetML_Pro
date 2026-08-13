"""Aislamiento entre usuarios en "Mis predicciones".

Bug real (2026-08-13): el endpoint devolvia TODAS las predicciones
guardadas, asi que cada usuario veia las de los demas. La app es
multiusuario, esto es una fuga de datos entre cuentas.

Reglas que fijan estos tests:
  - cada usuario ve solo lo suyo
  - las del sistema (usuario_id NULL) no se le muestran a nadie, pero
    siguen contando para las metricas del modelo
"""
from backend.db.database import SessionLocal
from backend.db.modelos import Prediccion, Usuario
from backend.repositories.prediccion_repo import PrediccionRepository

PARTIDO = 1547761  # existe en la base de desarrollo


def _limpiar(db, ids):
    db.query(Prediccion).filter(Prediccion.usuario_id.in_(ids)).delete(synchronize_session=False)
    db.query(Prediccion).filter(Prediccion.mercado == "test_sistema").delete(synchronize_session=False)
    db.query(Usuario).filter(Usuario.id.in_(ids)).delete(synchronize_session=False)
    db.commit()


def test_cada_usuario_ve_solo_sus_predicciones():
    db = SessionLocal()
    ids = [980001, 980002]
    try:
        _limpiar(db, ids)
        db.add(Usuario(id=980001, email="a@test.com", password_hash="x"))
        db.add(Usuario(id=980002, email="b@test.com", password_hash="x"))
        db.commit()

        repo = PrediccionRepository(db)
        repo.crear(partido_id=PARTIDO, mercado="local", prediccion="1X2 Local",
                   probabilidad=0.5, confianza=0.5, usuario_id=980001)
        repo.crear(partido_id=PARTIDO, mercado="btts_si", prediccion="BTTS Si",
                   probabilidad=0.6, confianza=0.6, usuario_id=980002)
        # del sistema: sin dueño
        repo.crear(partido_id=PARTIDO, mercado="test_sistema", prediccion="Sistema",
                   probabilidad=0.7, confianza=0.7)

        de_a = repo.listar(usuario_id=980001)
        de_b = repo.listar(usuario_id=980002)

        assert [p.mercado for p in de_a] == ["local"]
        assert [p.mercado for p in de_b] == ["btts_si"]
        # ninguno ve la del sistema ni la del otro
        assert "test_sistema" not in [p.mercado for p in de_a + de_b]
    finally:
        _limpiar(db, ids)
        db.close()


def test_sin_filtro_siguen_estando_todas_para_las_metricas():
    """El MLOps y la calibracion necesitan ver TODAS, incluidas las del
    sistema — es lo que mide si el modelo predice bien."""
    db = SessionLocal()
    ids = [980003]
    try:
        _limpiar(db, ids)
        db.add(Usuario(id=980003, email="c@test.com", password_hash="x"))
        db.commit()

        repo = PrediccionRepository(db)
        repo.crear(partido_id=PARTIDO, mercado="local", prediccion="1X2 Local",
                   probabilidad=0.5, confianza=0.5, usuario_id=980003)
        repo.crear(partido_id=PARTIDO, mercado="test_sistema", prediccion="Sistema",
                   probabilidad=0.7, confianza=0.7)

        mercados = [p.mercado for p in repo.listar(limite=500)]
        assert "local" in mercados and "test_sistema" in mercados
    finally:
        _limpiar(db, ids)
        db.close()
