import numpy as np

from backend.models.backtest_walk_forward import _metricas


def test_metricas_walk_forward_miden_calibracion_y_alta_confianza():
    y = np.array([0, 1, 2, 0])
    proba = np.array([
        [0.80, 0.10, 0.10],
        [0.20, 0.60, 0.20],
        [0.10, 0.20, 0.70],
        [0.20, 0.30, 0.50],
    ])

    resultado = _metricas(y, proba)

    assert resultado["accuracy"] == 0.75
    assert resultado["alta_confianza"]["n"] == 2
    assert resultado["alta_confianza"]["accuracy"] == 1.0
    assert resultado["log_loss"] > 0
    assert resultado["brier_multiclase"] > 0
