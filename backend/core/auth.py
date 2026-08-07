"""Autenticación JWT — hash de contraseñas (bcrypt) + emisión/validación
de tokens (PyJWT). Sin refresh tokens ni roles — un solo tipo de usuario,
alcanza para una app de uso personal/chico. Si hace falta multi-rol o
sesiones revocables más adelante, esto es el punto de partida a extender,
no una reescritura.
"""
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from backend.core.config import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def crear_token(usuario_id: int, email: str) -> str:
    expira = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expira_minutos)
    payload = {"sub": str(usuario_id), "email": email, "exp": expira}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algoritmo)


def verificar_token(token: str) -> dict | None:
    """Devuelve el payload si el token es válido, None si expiró o es inválido."""
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algoritmo])
    except jwt.PyJWTError:
        return None
