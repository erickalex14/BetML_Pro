from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.modelos import SesionRefresh, Usuario
from backend.core.auth import (
    crear_token, hash_password, hash_token, nuevo_jti,
    verificar_password, verificar_token,
)
from backend.core.config import get_settings
from backend.core.deps import get_usuario_actual
from backend.core.rate_limit import limiter

router = APIRouter()


class RegistroRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def password_cabe_en_bcrypt(cls, password: str) -> str:
        if len(password.encode("utf-8")) > 72:
            raise ValueError("La contraseña no puede superar 72 bytes")
        return password


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=72)

    @field_validator("password")
    @classmethod
    def password_cabe_en_bcrypt(cls, password: str) -> str:
        if len(password.encode("utf-8")) > 72:
            raise ValueError("La contraseña no puede superar 72 bytes")
        return password


class GoogleRequest(BaseModel):
    id_token: str = Field(min_length=20, max_length=10000)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=5000)


def _user_agent(request: Request | None) -> str | None:
    return request.headers.get("user-agent")[:500] if request else None


def _emitir_tokens(db: Session, usuario: Usuario, request: Request | None) -> dict:
    settings = get_settings()
    jti = nuevo_jti()
    refresh_token = crear_token(usuario.id, usuario.email, "refresh", jti)
    db.add(SesionRefresh(
        usuario_id=usuario.id,
        token_hash=hash_token(refresh_token),
        expira_en=datetime.utcnow() + timedelta(days=settings.jwt_refresh_dias),
        user_agent=_user_agent(request),
    ))
    usuario.ultimo_login = datetime.utcnow()
    db.commit()
    return {
        # El APK anterior no sabe refrescar. Mantenerle 7 días hasta que
        # sea reemplazado; el APK Fase 2 envía esta cabecera y recibe 15 min.
        "access_token": crear_token(
            usuario.id, usuario.email, "access",
            duracion_minutos=None if request and request.headers.get("X-BetML-Auth-Version") == "2"
            else 60 * 24 * 7,
        ),
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/registro", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def registro(request: Request, body: RegistroRequest, db: Session = Depends(get_db)):
    existente = db.query(Usuario).filter(Usuario.email == body.email).first()
    if existente:
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese email")

    usuario = Usuario(email=body.email, password_hash=hash_password(body.password))
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    return _emitir_tokens(db, usuario, request)


@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == body.email).first()

    # mismo mensaje de error para "no existe" y "password incorrecta" —
    # no revelar cuál de las dos cosas falló (evita enumerar emails
    # registrados probando contraseñas al voleo)
    if not usuario:
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    if usuario.password_hash is None:
        raise HTTPException(status_code=401, detail="Esta cuenta entra con Google")

    if not verificar_password(body.password, usuario.password_hash):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Cuenta desactivada")

    return _emitir_tokens(db, usuario, request)


@router.post("/google")
@limiter.limit("5/minute")
def google(request: Request, body: GoogleRequest, db: Session = Depends(get_db)):
    if not get_settings().google_client_id:
        raise HTTPException(status_code=503, detail="Login con Google no configurado")

    from backend.core.google_auth import verificar_id_token_google
    try:
        datos = verificar_id_token_google(body.id_token)
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Token de Google inválido")

    if datos.get("email_verified") is not True:
        raise HTTPException(status_code=401, detail="Google no verificó este email")

    google_sub = datos.get("sub")
    email = (datos.get("email") or "").lower()
    if not google_sub or not email:
        raise HTTPException(status_code=401, detail="Token de Google incompleto")

    usuario = db.query(Usuario).filter(Usuario.google_sub == google_sub).first()
    if usuario is None:
        usuario = db.query(Usuario).filter(Usuario.email == email).first()
        if usuario is None:
            usuario = Usuario(email=email, password_hash=None)
            db.add(usuario)
        usuario.google_sub = google_sub

    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Cuenta desactivada")

    usuario.nombre = datos.get("name") or usuario.nombre
    usuario.avatar_url = datos.get("picture") or usuario.avatar_url
    usuario.email_verificado = True
    db.flush()
    return _emitir_tokens(db, usuario, request)


@router.post("/refresh")
@limiter.limit("10/minute")
def refresh(request: Request, body: RefreshRequest, db: Session = Depends(get_db)):
    payload = verificar_token(body.refresh_token, "refresh")
    if payload is None:
        raise HTTPException(status_code=401, detail="Refresh token inválido o expirado")

    sesion = db.query(SesionRefresh).filter(
        SesionRefresh.token_hash == hash_token(body.refresh_token)
    ).first()
    usuario_id = int(payload["sub"])
    if sesion is None or sesion.usuario_id != usuario_id:
        raise HTTPException(status_code=401, detail="Refresh token inválido o expirado")

    if sesion.revocada:
        db.query(SesionRefresh).filter(SesionRefresh.usuario_id == usuario_id).update(
            {SesionRefresh.revocada: True}, synchronize_session=False
        )
        db.commit()
        raise HTTPException(status_code=401, detail="Refresh token reutilizado; sesiones revocadas")

    if sesion.expira_en <= datetime.utcnow():
        sesion.revocada = True
        db.commit()
        raise HTTPException(status_code=401, detail="Refresh token inválido o expirado")

    usuario = db.get(Usuario, usuario_id)
    if usuario is None or not usuario.activo:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")

    sesion.revocada = True
    db.flush()
    return _emitir_tokens(db, usuario, request)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(body: RefreshRequest, db: Session = Depends(get_db)):
    sesion = db.query(SesionRefresh).filter(
        SesionRefresh.token_hash == hash_token(body.refresh_token)
    ).first()
    if sesion:
        sesion.revocada = True
        db.commit()


@router.get("/me")
def me(usuario: Usuario = Depends(get_usuario_actual)):
    return {"id": usuario.id, "email": usuario.email, "nombre": usuario.nombre,
            "avatar_url": usuario.avatar_url, "creado_en": usuario.creado_en}
