"""Contador compartido de requests a API-Football por día — el plan
free da 100/día, reset a medianoche UTC (confirmado vía /status el
2026-08-12: {"current": 99, "limit_day": 100} con nada más que uso
normal + pruebas manuales de esa misma sesión).

Sin esto cada job decidía solo si le tocaba gastar y nada frenaba el
total combinado entre todos — job_odds_en_vivo/job_partidos_en_vivo
corriendo cada 5-15 min durante horas de partidos en vivo, más
job_estadisticas (hasta 80) y job_odds (hasta 40) pre-partido, sumados
pasan los 300/día en el peor caso.

registrar_uso() se llama desde api_client.get() en CADA intento (éxito o
error) — API-Football cuenta el request igual. No se usa /status para
chequear cuánto queda (eso también gastaría cuota) — se lleva la cuenta
acá mismo, en DB."""
import logging
from datetime import datetime, timezone
from backend.db.database import SessionLocal, crear_tablas
from backend.db.modelos import PresupuestoApiFootball

log = logging.getLogger(__name__)

LIMITE_DIARIO = 100


def _hoy_utc():
    # API-Football resetea a medianoche UTC, no a medianoche Guayaquil
    # (UTC-5) — el contador tiene que usar el mismo día que ellos.
    return datetime.now(timezone.utc).date()


def registrar_uso() -> int:
    """Suma 1 al contador de hoy (crea la fila si hace falta). Devuelve
    el total usado hoy después de sumar."""
    crear_tablas()
    db = SessionLocal()
    try:
        hoy = _hoy_utc()
        fila = db.get(PresupuestoApiFootball, hoy)
        if fila is None:
            fila = PresupuestoApiFootball(fecha=hoy, usados=0)
            db.add(fila)
        fila.usados += 1
        db.commit()
        return fila.usados
    finally:
        db.close()


def restantes() -> int:
    crear_tablas()
    db = SessionLocal()
    try:
        fila = db.get(PresupuestoApiFootball, _hoy_utc())
        usados = fila.usados if fila else 0
        return max(0, LIMITE_DIARIO - usados)
    finally:
        db.close()


def hay_presupuesto(minimo: int) -> bool:
    """True si queda al menos `minimo` de presupuesto hoy. Los jobs en
    vivo (baja prioridad, corren muy seguido) piden un mínimo alto para
    frenarse temprano y dejarle lugar a los jobs nocturnos críticos
    (fixtures/estadísticas/odds pre-partido, sin los cuales no hay nada
    que predecir mañana)."""
    return restantes() >= minimo
