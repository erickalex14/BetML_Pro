from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.modelos import Usuario
from backend.core.auth import hash_password, verificar_password, crear_token
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

    token = crear_token(usuario.id, usuario.email)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == body.email).first()

    # mismo mensaje de error para "no existe" y "password incorrecta" —
    # no revelar cuál de las dos cosas falló (evita enumerar emails
    # registrados probando contraseñas al voleo)
    if not usuario or not verificar_password(body.password, usuario.password_hash):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Cuenta desactivada")

    token = crear_token(usuario.id, usuario.email)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def me(usuario: Usuario = Depends(get_usuario_actual)):
    return {"id": usuario.id, "email": usuario.email, "creado_en": usuario.creado_en}
