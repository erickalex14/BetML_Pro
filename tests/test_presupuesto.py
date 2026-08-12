"""Contador de presupuesto diario de API-Football — evita repetir el
incidente real del 2026-08-12 (cuenta llegó a 100/100 sin que ningún job
lo supiera, porque nada frenaba el total combinado). Usa fechas falsas
lejanas (vía monkeypatch de _hoy_utc) para no tocar el contador real del
día en que corran los tests — y borra la fila antes de cada test, porque
la DB de dev es real y persiste entre corridas de pytest (sin este borrado
la segunda corrida ve la fila con usados=100 que dejó la primera y falla
sin que el código tenga ningún bug real)."""
from datetime import date
import backend.pipeline.presupuesto as presupuesto
from backend.db.database import SessionLocal
from backend.db.modelos import PresupuestoApiFootball


def _limpiar(fecha):
    db = SessionLocal()
    fila = db.get(PresupuestoApiFootball, fecha)
    if fila is not None:
        db.delete(fila)
        db.commit()
    db.close()


def test_registrar_uso_suma_y_restantes_descuenta(monkeypatch):
    fecha = date(2099, 1, 1)
    _limpiar(fecha)
    monkeypatch.setattr(presupuesto, "_hoy_utc", lambda: fecha)
    restantes_antes = presupuesto.restantes()

    presupuesto.registrar_uso()
    presupuesto.registrar_uso()

    assert presupuesto.restantes() == restantes_antes - 2


def test_hay_presupuesto_respeta_minimo(monkeypatch):
    fecha = date(2099, 1, 2)
    _limpiar(fecha)
    monkeypatch.setattr(presupuesto, "_hoy_utc", lambda: fecha)
    assert presupuesto.hay_presupuesto(1)  # día fresco, nadie gastó nada

    for _ in range(100):
        presupuesto.registrar_uso()

    assert presupuesto.restantes() == 0
    assert not presupuesto.hay_presupuesto(1)


def test_restantes_nunca_negativo(monkeypatch):
    fecha = date(2099, 1, 3)
    _limpiar(fecha)
    monkeypatch.setattr(presupuesto, "_hoy_utc", lambda: fecha)
    for _ in range(105):  # pasarse del límite a propósito
        presupuesto.registrar_uso()
    assert presupuesto.restantes() == 0
