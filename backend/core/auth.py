"""Autenticación JWT — hash de contraseñas (bcrypt) + emisión/validación
de tokens (PyJWT). Sin refresh tokens ni roles — un solo tipo de usuario,
alcanza para una app de uso personal/chico. Si hace falta multi-rol o
sesiones revocables más adelante, esto es el punto de partida a extender,
no una reescritura.
"""
import hashlib
import secrets
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from backend.core.config import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def crear_token(usuario_id: int, email: str, tipo: str = "access", jti: str | None = None,
                duracion_minutos: int | None = None) -> str:
    ahora = datetime.now(timezone.utc)
    expira = ahora + (timedelta(minutes=duracion_minutos or settings.jwt_expira_minutos)
                      if tipo == "access" else timedelta(days=settings.jwt_refresh_dias))
    payload = {"sub": str(usuario_id), "email": email, "iat": ahora,
               "exp": expira, "type": tipo}
    if jti:
        payload["jti"] = jti
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algoritmo)


def verificar_token(token: str, tipo: str = "access") -> dict | None:
    """Devuelve el payload si el token es válido, None si expiró o es inválido."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algoritmo])
        tipo_token = payload.get("type")
        # Compatibilidad temporal con JWT del APK ya distribuido antes de
        # Fase 2: no tenían `type`, pero sí eran access tokens firmados.
        return payload if tipo_token == tipo or (tipo == "access" and tipo_token is None) else None
    except jwt.PyJWTError:
        return None


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def nuevo_jti() -> str:
    return secrets.token_urlsafe(32)
