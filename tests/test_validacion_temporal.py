import pandas as pd
import pytest

from backend.models.validacion import (
    brier_confianza_elegida, division_temporal, ventanas_walk_forward)


def _dataset(n=20):
    return pd.DataFrame({
        "partido_id": list(range(n)),
        "fecha": pd.date_range("2026-01-01", periods=n, freq="D"),
        "resultado": [i % 3 for i in range(n)],
    })


def test_validacion_siempre_es_posterior_al_entrenamiento():
    train, val = division_temporal(_dataset())
    assert len(train) == 16
    assert len(val) == 4
    assert train["fecha"].max() < val["fecha"].min()


def test_no_parte_partidos_del_mismo_dia():
    df = _dataset()
    df.loc[15:17, "fecha"] = pd.Timestamp("2026-01-17")
    train, val = division_temporal(df)
    assert set(train["fecha"]).isdisjoint(set(val["fecha"]))


def test_rechaza_dataset_sin_fecha():
    with pytest.raises(ValueError, match="fecha"):
        division_temporal(_dataset().drop(columns="fecha"))


def test_walk_forward_expande_train_y_no_solapa_fechas():
    ventanas = ventanas_walk_forward(_dataset(40), n_ventanas=4)

    assert len(ventanas) == 4
    tamanos_train = [len(train) for train, _ in ventanas]
    assert tamanos_train == sorted(tamanos_train)
    assert len(set(tamanos_train)) == 4
    for train, val in ventanas:
        assert train["fecha"].max() < val["fecha"].min()


def test_walk_forward_no_parte_un_dia_con_varios_partidos():
    df = _dataset(40)
    df.loc[20:22, "fecha"] = pd.Timestamp("2026-01-22")

    for train, val in ventanas_walk_forward(df, n_ventanas=4):
        assert set(train["fecha"]).isdisjoint(set(val["fecha"]))


def test_brier_confianza_penaliza_seguridad_equivocada():
    y = [0, 1]
    bien = [[0.8, 0.1, 0.1], [0.1, 0.8, 0.1]]
    mal = [[0.1, 0.8, 0.1], [0.8, 0.1, 0.1]]

    assert brier_confianza_elegida(y, bien) < brier_confianza_elegida(y, mal)
