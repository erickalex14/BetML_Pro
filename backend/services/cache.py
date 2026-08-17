from datetime import datetime, timedelta

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from backend.db.modelos import CacheJson
from backend.pipeline.config import fecha_hoy_partidos


def obtener_cache(db: Session, clave: str):
    entrada = db.get(CacheJson, clave)
    if entrada is None:
        return None
    if entrada.expira_en <= datetime.utcnow():
        db.delete(entrada)
        db.commit()
        return None
    return entrada.payload


def guardar_cache(db: Session, clave: str, payload, ttl: timedelta) -> None:
    entrada = db.get(CacheJson, clave)
    if entrada is None:
        entrada = CacheJson(clave=clave)
        db.add(entrada)
    entrada.payload = jsonable_encoder(payload)
    entrada.expira_en = datetime.utcnow() + ttl
    db.commit()


def invalidar_cache_dia(db: Session) -> None:
    hoy = fecha_hoy_partidos()
    for clave in (f"partidos_hoy:{hoy}", f"recomendadas:{hoy}"):
        entrada = db.get(CacheJson, clave)
        if entrada is not None:
            db.delete(entrada)
    db.commit()
