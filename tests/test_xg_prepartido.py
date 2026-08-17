from backend.features.medias_liga import estimar_xg_prepartido


MEDIAS = {"xg_local": 1.5, "xg_visit": 1.2}


def test_sin_historial_usa_medias_reales_y_no_probabilidades_1x2():
    vacio = {"xg_favor": 0.0, "xg_contra": 0.0, "n_con_xg": 0}

    local, visit, fuente = estimar_xg_prepartido(vacio, vacio, MEDIAS)

    assert local == 1.5
    assert visit == 1.2
    assert "insuficientes" in fuente


def test_combina_ataque_defensa_con_regresion_a_media():
    local_stats = {"xg_favor": 2.0, "xg_contra": 0.8, "n_con_xg": 8}
    visit_stats = {"xg_favor": 1.0, "xg_contra": 1.8, "n_con_xg": 8}

    local, visit, fuente = estimar_xg_prepartido(local_stats, visit_stats, MEDIAS)

    assert 1.5 < local < 1.9
    assert 0.9 < visit < 1.2
    assert "regresión" in fuente


def test_historial_parcial_no_se_declara_apto_como_completo():
    local_stats = {"xg_favor": 2.0, "xg_contra": 1.0, "n_con_xg": 3}
    visit_stats = {"xg_favor": 0.0, "xg_contra": 0.0, "n_con_xg": 0}

    _, _, fuente = estimar_xg_prepartido(local_stats, visit_stats, MEDIAS)

    assert "parcial" in fuente


def test_xg_extremo_queda_acotado():
    extremo = {"xg_favor": 20.0, "xg_contra": 20.0, "n_con_xg": 1000}

    local, visit, _ = estimar_xg_prepartido(extremo, extremo, MEDIAS)

    assert local == 3.5
    assert visit == 3.5
