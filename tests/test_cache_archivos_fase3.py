import os

import joblib

from backend.models.calibracion import cargar_calibracion


def test_calibracion_se_recarga_si_cambia_mtime(tmp_path):
    ruta = tmp_path / "calibracion.pkl"
    joblib.dump({"version": 1}, ruta)
    assert cargar_calibracion(ruta)["version"] == 1

    mtime_anterior = ruta.stat().st_mtime_ns
    joblib.dump({"version": 2, "relleno": "x" * 100}, ruta)
    os.utime(ruta, ns=(mtime_anterior + 1_000_000, mtime_anterior + 1_000_000))
    assert cargar_calibracion(ruta)["version"] == 2
