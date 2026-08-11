"""Por qué el modelo predijo lo que predijo — sin llamar a un LLM en cada
request (latencia + costo + inventaría números). En cambio: toma las
mismas features que vio XGBoost para ESTE partido (construir_features_partido,
las que ya se calculan para predecir) y las importancias reales del árbol
entrenado (modelo.feature_importances_, ya viene con el .pkl cargado — no
hace falta guardar nada nuevo), arma oraciones con los números reales.

Determinístico y trazable: cada factor que se muestra es una comparación
local-vs-visitante de un feature que el modelo efectivamente usó, ordenado
por cuánto pesa ese feature en el árbol.
"""
# (feature_local, feature_visit, etiqueta, formato, invertido)
# invertido=True cuando un valor MENOR es mejor (goles en contra, xG en contra)
_PARES = [
    ("forma_local_puntos", "forma_visit_puntos", "forma reciente", "{:.0f} pts en los últimos 5", False),
    ("forma_local_gf", "forma_visit_gf", "gol a favor reciente", "{:.1f} goles/partido", False),
    ("forma_local_gc", "forma_visit_gc", "goles recibidos", "{:.1f} goles/partido", True),
    ("win_rate_local", "win_rate_visit", "ratio de victorias", "{:.0%}", False),
    ("xg_favor_local", "xg_favor_visit", "peligro ofensivo (xG)", "{:.2f} xG/partido", False),
    ("xg_contra_local", "xg_contra_visit", "solidez defensiva (xG recibido)", "{:.2f} xG/partido", True),
    ("tiros_favor_local", "tiros_favor_visit", "tiros por partido", "{:.1f}", False),
    ("tiros_arco_fav_local", "tiros_arco_fav_visit", "tiros al arco", "{:.1f}", False),
    ("corners_fav_local", "corners_fav_visit", "córners a favor", "{:.1f}", False),
    ("presiones_local", "presiones_visit", "presión defensiva", "{:.1f}", False),
    ("posesion_local", "posesion_visit", "posesión", "{:.0%}", False),
    ("rating_local", "rating_visit", "rating promedio del plantel", "{:.2f}", False),
]

# margen relativo mínimo para considerar un factor "parejo" en vez de forzar
# un ganador con ruido de decimales
_UMBRAL_PAREJO = 0.05


def generar_resumen(features: dict, importancias: dict, nombre_local: str,
                     nombre_visit: str, top_n: int = 5) -> list[dict]:
    candidatos = []
    for feat_local, feat_visit, etiqueta, formato, invertido in _PARES:
        v_local = features.get(feat_local)
        v_visit = features.get(feat_visit)
        if v_local is None or v_visit is None:
            continue

        peso = importancias.get(feat_local, 0.0) + importancias.get(feat_visit, 0.0)
        candidatos.append((peso, feat_local, feat_visit, etiqueta, formato, invertido, v_local, v_visit))

    candidatos.sort(key=lambda c: c[0], reverse=True)

    factores = []
    for peso, feat_local, feat_visit, etiqueta, formato, invertido, v_local, v_visit in candidatos[:top_n]:
        mayor_es_local = v_local > v_visit
        if invertido:
            mayor_es_local = not mayor_es_local

        base = max(abs(v_local), abs(v_visit), 1e-6)
        parejo = abs(v_local - v_visit) / base < _UMBRAL_PAREJO

        if parejo:
            favorece = "parejo"
            texto = f"{etiqueta.capitalize()} pareja: {formato.format(v_local)} vs {formato.format(v_visit)}"
        else:
            equipo_mejor = nombre_local if mayor_es_local else nombre_visit
            v_mejor = v_local if mayor_es_local else v_visit
            v_peor = v_visit if mayor_es_local else v_local
            favorece = "local" if mayor_es_local else "visitante"
            texto = f"{equipo_mejor} tiene mejor {etiqueta}: {formato.format(v_mejor)} vs {formato.format(v_peor)}"

        factores.append({
            "factor": etiqueta,
            "favorece": favorece,
            "texto": texto,
            "importancia": round(float(peso), 4),
        })

    return factores


def generar_resumen_h2h(features: dict, nombre_local: str, nombre_visit: str) -> str | None:
    wins_local = features.get("h2h_wins_local")
    empates = features.get("h2h_empates")
    wins_visit = features.get("h2h_wins_visit")
    if wins_local is None or empates is None or wins_visit is None:
        return None
    total = wins_local + empates + wins_visit
    if total == 0:
        return None
    return (f"En los enfrentamientos directos: {nombre_local} ganó {int(wins_local)}, "
            f"{int(empates)} empate(s), {nombre_visit} ganó {int(wins_visit)} "
            f"(de {int(total)} jugados)")
