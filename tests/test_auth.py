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
from backend.db.modelos import Usuario
from backend.api.routes.auth import registro, login, RegistroRequest, LoginRequest

EMAIL_TEST = "pytest-caveman@test.com"


def _registro(body, db):
    return registro.__wrapped__(None, body, db)


def _login(body, db):
    return login.__wrapped__(None, body, db)


@pytest.fixture
def db():
    session = SessionLocal()
    session.query(Usuario).filter(Usuario.email == EMAIL_TEST).delete()
    session.commit()
    yield session
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
