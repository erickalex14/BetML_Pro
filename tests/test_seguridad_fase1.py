from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.routes import predicciones
from backend.api.routes.predicciones import ParlayRequest, SeleccionParlay
from backend.core.auth import crear_token, hash_password
from backend.core.rate_limit import limiter
from backend.db.database import SessionLocal
from backend.db.modelos import Parlay, ParlaySeleccion, Usuario
from backend.services.prediccion_service import PrediccionService


EMAIL = "fase1@test.com"


def _usuario_y_token():
    db = SessionLocal()
    try:
        db.query(Usuario).filter(Usuario.email == EMAIL).delete()
        usuario = Usuario(email=EMAIL, password_hash=hash_password("claveSegura123"))
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        return usuario.id, crear_token(usuario.id, usuario.email)
    finally:
        db.close()


def test_topes_caros_y_rate_limit():
    limiter.reset()
    usuario_id, token = _usuario_y_token()
    client = TestClient(app)
    auth = {"Authorization": f"Bearer {token}"}

    parlay = {
        "selecciones": [{"partido_id": 1, "mercado": "local"}] * 50,
    }
    assert client.post("/predicciones/combinada", json=parlay, headers=auth).status_code == 422

    archivo = {"imagen": ("captura.png", b"x" * (5 * 1024 * 1024 + 1), "image/png")}
    assert client.post("/predicciones/analizar-captura", files=archivo, headers=auth).status_code == 413

    intentos = [
        client.post("/auth/login", json={"email": EMAIL, "password": "incorrecta"})
        for _ in range(6)
    ]
    assert [r.status_code for r in intentos[:5]] == [401] * 5
    assert intentos[5].status_code == 429

    db = SessionLocal()
    try:
        db.query(Usuario).filter(Usuario.id == usuario_id).delete()
        db.commit()
    finally:
        db.close()


def test_parlay_guardado_pertenece_al_usuario(monkeypatch):
    usuario_id, _ = _usuario_y_token()
    db = SessionLocal()
    usuario = db.get(Usuario, usuario_id)
    monkeypatch.setattr(PrediccionService, "predecir", lambda *_: {"prob_local": 0.7})
    monkeypatch.setattr(predicciones, "_correr_montecarlo_partido", lambda *_: ({}, "test"))

    import backend.models.kelly as kelly
    import backend.models.odds_service as odds_service
    monkeypatch.setattr(
        kelly,
        "construir_lista_mercados",
        lambda *_: [("1X2 Local", 0.7, "odds_local", "local")],
    )
    monkeypatch.setattr(odds_service, "obtener_mejores_odds", lambda *_: {})

    body = ParlayRequest(selecciones=[
        SeleccionParlay(partido_id=1000, mercado="local", cuota=2.0),
        SeleccionParlay(partido_id=1001, mercado="local", cuota=2.0),
    ])
    resultado = predicciones.apuesta_combinada.__wrapped__(None, body, db, usuario)
    parlay = db.get(Parlay, resultado["parlay_id"])
    try:
        assert parlay.usuario_id == usuario_id
    finally:
        db.query(ParlaySeleccion).filter(ParlaySeleccion.parlay_id == parlay.id).delete()
        db.delete(parlay)
        db.query(Usuario).filter(Usuario.id == usuario_id).delete()
        db.commit()
        db.close()
