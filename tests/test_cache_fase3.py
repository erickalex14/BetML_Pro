from datetime import timedelta

from backend.db.database import SessionLocal
from backend.db.modelos import CacheJson
from backend.services.cache import guardar_cache, obtener_cache


def test_cache_json_compartido_guarda_y_recupera():
    db = SessionLocal()
    clave = "pytest:cache:fase3"
    try:
        db.query(CacheJson).filter(CacheJson.clave == clave).delete()
        db.commit()
        guardar_cache(db, clave, {"lista": [1, 2], "ok": True}, timedelta(minutes=1))
        assert obtener_cache(db, clave) == {"lista": [1, 2], "ok": True}
    finally:
        db.query(CacheJson).filter(CacheJson.clave == clave).delete()
        db.commit()
        db.close()


def test_cache_expirado_se_elimina():
    db = SessionLocal()
    clave = "pytest:cache:expirado"
    try:
        guardar_cache(db, clave, {"viejo": True}, timedelta(seconds=-1))
        assert obtener_cache(db, clave) is None
        assert db.get(CacheJson, clave) is None
    finally:
        db.close()
