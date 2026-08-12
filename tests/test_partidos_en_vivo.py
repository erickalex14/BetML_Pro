"""La guardia de job_partidos_en_vivo decide si vale la pena gastar un
request de los 100/día del plan free. _necesita_actualizacion es lógica
pura (sin DB) justo para poder testear los 3 casos sin que partidos
reales de hoy en la BD contaminen el resultado."""
from datetime import datetime, timedelta
from types import SimpleNamespace
from backend.pipeline.job_partidos_en_vivo import _necesita_actualizacion


def _partido(estado: str, fecha: datetime):
    return SimpleNamespace(estado=estado, fecha=fecha)


def test_sin_partidos_no_hace_falta_actualizar():
    assert _necesita_actualizacion([], datetime.utcnow()) is False


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
