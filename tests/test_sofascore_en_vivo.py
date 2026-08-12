"""Traducción de un evento de Sofascore a nuestro modelo — lógica pura,
sin DB ni red. Cubre el bug del marcador con penales (visto real:
Arsenal vs Como terminó 1-1 pero "current" decía 5-4 porque sumaba la
tanda) y el mapeo de estado/minuto."""
from backend.pipeline.sofascore.job_sofascore_en_vivo import (
    _estado_desde_evento, _goles_desde, _minuto_desde_evento)


def test_goles_ignora_penales_y_usa_tiempo_reglamentario():
    # caso REAL: Arsenal 1-1 Como, definido 5-4 por penales
    marcador = {"current": 5, "display": 1, "normaltime": 1, "penalties": 4}
    assert _goles_desde(marcador) == 1


def test_goles_cae_a_current_si_no_hay_nada_mejor():
    assert _goles_desde({"current": 2}) == 2
    assert _goles_desde({}) is None
    assert _goles_desde(None) is None


def test_estado_mapea_tipos_simples():
    assert _estado_desde_evento({"status": {"type": "notstarted"}}, "NS") == "NS"
    assert _estado_desde_evento({"status": {"type": "finished"}}, "2H") == "FT"
    assert _estado_desde_evento({"status": {"type": "postponed"}}, "NS") == "PST"


def test_estado_en_juego_usa_la_descripcion_del_periodo():
    def ev(desc):
        return {"status": {"type": "inprogress", "description": desc}}

    assert _estado_desde_evento(ev("1st half"), "NS") == "1H"
    assert _estado_desde_evento(ev("2nd half"), "1H") == "2H"
    assert _estado_desde_evento(ev("Halftime"), "1H") == "HT"
    assert _estado_desde_evento(ev("Extra time"), "2H") == "ET"


def test_estado_en_juego_sin_descripcion_no_inventa_periodo():
    ev = {"status": {"type": "inprogress", "description": "???"}}
    # si ya veníamos en 2H, se respeta en vez de retroceder a 1H
    assert _estado_desde_evento(ev, "2H") == "2H"
    # si no había nada en vivo todavía, arranca en 1H
    assert _estado_desde_evento(ev, "NS") == "1H"


def test_minuto_solo_en_periodos_jugables_y_descarta_absurdos():
    import time
    ahora = time.time()
    # 10 min y medio: evita que el redondeo dependa de los milisegundos
    # que tarda el test en llegar a la aserción
    ev_reciente = {"time": {"currentPeriodStartTimestamp": ahora - 630}}

    # convención del fútbol: a los 10:30 se está jugando el minuto 11
    assert _minuto_desde_evento(ev_reciente, "1H") == 11
    assert _minuto_desde_evento(ev_reciente, "2H") == 56  # 11 + offset 45
    assert _minuto_desde_evento(ev_reciente, "HT") is None
    assert _minuto_desde_evento(ev_reciente, "FT") is None
    assert _minuto_desde_evento({"time": {}}, "1H") is None

    # partido viejo: el cálculo daría cientos de minutos — se descarta
    ev_viejo = {"time": {"currentPeriodStartTimestamp": ahora - 100000}}
    assert _minuto_desde_evento(ev_viejo, "1H") is None

    # timestamp futuro (reloj desfasado): tampoco inventa un minuto
    assert _minuto_desde_evento({"time": {"currentPeriodStartTimestamp": ahora + 600}}, "1H") is None
