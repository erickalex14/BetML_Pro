"""Tests de autenticación — hash/JWT y el flujo completo de
registro/login/protección de rutas.

Usa la BD real configurada (no hay BD de test separada todavía — ver
ponytail: agregar una si el equipo crece y esto empieza a chocar con
datos reales) — cada test limpia el usuario que crea."""
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from backend.core.auth import hash_password, verificar_password, crear_token, verificar_token
from backend.core.deps import get_usuario_actual
from backend.db.database import SessionLocal
from backend.db.modelos import SesionRefresh, Usuario
from backend.api.routes.auth import (
    GoogleRequest, LoginRequest, RefreshRequest, RegistroRequest,
    google, login, refresh, registro,
)

EMAIL_TEST = "pytest-caveman@test.com"


def _registro(body, db):
    return registro.__wrapped__(None, body, db)


def _login(body, db):
    return login.__wrapped__(None, body, db)


@pytest.fixture
def db():
    session = SessionLocal()
    ids = [u.id for u in session.query(Usuario.id).filter(Usuario.email == EMAIL_TEST)]
    if ids:
        session.query(SesionRefresh).filter(SesionRefresh.usuario_id.in_(ids)).delete(synchronize_session=False)
    session.query(Usuario).filter(Usuario.email == EMAIL_TEST).delete()
    session.commit()
    yield session
    ids = [u.id for u in session.query(Usuario.id).filter(Usuario.email == EMAIL_TEST)]
    if ids:
        session.query(SesionRefresh).filter(SesionRefresh.usuario_id.in_(ids)).delete(synchronize_session=False)
    session.query(Usuario).filter(Usuario.email == EMAIL_TEST).delete()
    session.commit()
    session.close()


def test_hash_password_no_guarda_texto_plano():
    h = hash_password("miPassword123")
    assert h != "miPassword123"
    assert verificar_password("miPassword123", h)
    assert not verificar_password("otraCosa", h)


def test_token_roundtrip():
    tok = crear_token(42, "test@x.com")
    payload = verificar_token(tok)
    assert payload["sub"] == "42"
    assert payload["email"] == "test@x.com"


def test_token_invalido_rechazado():
    assert verificar_token("token-truchado") is None


def test_registro_login_flujo_completo(db):
    r = _registro(RegistroRequest(email=EMAIL_TEST, password="claveSegura123"), db)
    assert "access_token" in r
    assert "refresh_token" in r

    usuario_db = db.query(Usuario).filter(Usuario.email == EMAIL_TEST).first()
    assert usuario_db.password_hash != "claveSegura123"

    r2 = _login(LoginRequest(email=EMAIL_TEST, password="claveSegura123"), db)
    assert "access_token" in r2


def test_login_password_incorrecta_da_401(db):
    _registro(RegistroRequest(email=EMAIL_TEST, password="claveSegura123"), db)
    with pytest.raises(HTTPException) as exc:
        _login(LoginRequest(email=EMAIL_TEST, password="claveMALA"), db)
    assert exc.value.status_code == 401


def test_get_usuario_actual_con_token_valido(db):
    r = _registro(RegistroRequest(email=EMAIL_TEST, password="claveSegura123"), db)
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=r["access_token"])
    usuario = get_usuario_actual(creds, db)
    assert usuario.email == EMAIL_TEST


def test_get_usuario_actual_con_token_invalido_da_401(db):
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="basura")
    with pytest.raises(HTTPException) as exc:
        get_usuario_actual(creds, db)
    assert exc.value.status_code == 401


def test_refresh_rota_y_detecta_reutilizacion(db):
    tokens = _registro(RegistroRequest(email=EMAIL_TEST, password="claveSegura123"), db)
    nuevos = refresh.__wrapped__(None, RefreshRequest(refresh_token=tokens["refresh_token"]), db)
    assert nuevos["refresh_token"] != tokens["refresh_token"]

    with pytest.raises(HTTPException) as exc:
        refresh.__wrapped__(None, RefreshRequest(refresh_token=tokens["refresh_token"]), db)
    assert exc.value.status_code == 401

    with pytest.raises(HTTPException):
        refresh.__wrapped__(None, RefreshRequest(refresh_token=nuevos["refresh_token"]), db)


def test_google_enlaza_misma_cuenta_por_email_verificado(db, monkeypatch):
    tokens = _registro(RegistroRequest(email=EMAIL_TEST, password="claveSegura123"), db)
    usuario_antes = db.query(Usuario).filter(Usuario.email == EMAIL_TEST).one()
    usuario_id = usuario_antes.id

    import backend.core.google_auth as google_auth
    monkeypatch.setattr(google_auth, "verificar_id_token_google", lambda _: {
        "sub": "google-sub-test", "email": EMAIL_TEST,
        "email_verified": True, "name": "Usuario Test",
    })
    settings = __import__("backend.api.routes.auth", fromlist=["get_settings"]).get_settings()
    anterior = settings.google_client_id
    settings.google_client_id = "client-test"
    try:
        respuesta = google.__wrapped__(None, GoogleRequest(id_token="x" * 20), db)
    finally:
        settings.google_client_id = anterior

    db.expire_all()
    usuario_despues = db.query(Usuario).filter(Usuario.email == EMAIL_TEST).one()
    assert respuesta["refresh_token"]
    assert usuario_despues.id == usuario_id
    assert usuario_despues.google_sub == "google-sub-test"
    assert usuario_despues.password_hash is not None
