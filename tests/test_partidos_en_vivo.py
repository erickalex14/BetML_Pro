"""La guardia de job_partidos_en_vivo decide si vale la pena gastar un
request de los 100/día del plan free. _necesita_actualizacion es lógica
pura (sin DB) justo para poder testear los 3 casos sin que partidos
reales de hoy en la BD contaminen el resultado."""
from datetime import datetime, timedelta
from types import SimpleNamespace
from backend.pipeline.job_partidos_en_vivo import _necesita_actualizacion


def _partido(estado: str, fecha: datetime):
    return SimpleNamespace(estado=estado, fecha=fecha)


def test_solo_partidos_futuros_no_hace_falta_actualizar():
    ahora = datetime.utcnow()
    partidos = [_partido("NS", ahora + timedelta(hours=3))]
    assert _necesita_actualizacion(partidos, ahora) is False


def test_solo_partidos_ya_terminados_no_hace_falta_actualizar():
    ahora = datetime.utcnow()
    partidos = [_partido("FT", ahora - timedelta(hours=2))]
    assert _necesita_actualizacion(partidos, ahora) is False


def test_partido_en_vivo_dispara_actualizacion():
    ahora = datetime.utcnow()
    partidos = [_partido("1H", ahora - timedelta(minutes=30))]
    assert _necesita_actualizacion(partidos, ahora) is True


def test_partido_ns_con_hora_pasada_dispara_actualizacion():
    ahora = datetime.utcnow()
    partidos = [_partido("NS", ahora - timedelta(minutes=20))]  # debería haber arrancado
    assert _necesita_actualizacion(partidos, ahora) is True


def test_dia_sin_partidos_dispara_actualizacion():
    """Bug real del 13/08/2026: ese día quedó con CERO partidos en la
    base y la app mostraba "no hay partidos hoy".

    La agenda baja "hoy" a las 23:55 y "mañana" a las 00:45, así que los
    partidos del día en curso salen del 00:45 del día anterior; si el
    scheduler está caído en esa ventana, el día se pierde. La red de
    seguridad no podía recuperarlo porque su guardia era circular: con
    la lista vacía devolvía False, o sea "no hay nada que actualizar", y
    entonces nunca iba a buscar los partidos que faltaban.
    """
    assert _necesita_actualizacion([], datetime.utcnow()) is True
