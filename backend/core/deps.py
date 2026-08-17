"""Dependencias de FastAPI para proteger rutas con JWT.

Uso: agregar `usuario: Usuario = Depends(get_usuario_actual)` a
cualquier endpoint que deba requerir login (ver predicciones.py/partidos.py).
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.modelos import Usuario
from backend.core.auth import verificar_token

_bearer = HTTPBearer()


def get_usuario_actual(
    credenciales: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    payload = verificar_token(credenciales.credentials, "access")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    usuario = db.get(Usuario, int(payload["sub"]))
    if usuario is None or not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return usuario
