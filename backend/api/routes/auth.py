from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.modelos import Usuario
from backend.core.auth import hash_password, verificar_password, crear_token
from backend.core.deps import get_usuario_actual

router = APIRouter()


class RegistroRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/registro", status_code=status.HTTP_201_CREATED)
def registro(body: RegistroRequest, db: Session = Depends(get_db)):
    if len(body.password) < 8:
        raise HTTPException(status_code=422, detail="La contraseña necesita al menos 8 caracteres")

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
def login(body: LoginRequest, db: Session = Depends(get_db)):
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
