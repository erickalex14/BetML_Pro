"""Extrae equipos y mercados de una captura de pantalla de un parley
(bet builder) — 100% gratis, EasyOCR corre local sobre el torch que ya
está instalado, sin API externa ni costo por imagen.

# ponytail: esto es heurístico (regex + palabras clave), no "entiende"
# la imagen como una IA con visión — lee texto y lo clasifica con
# patrones. Funciona con capturas limpias en español/inglés con el
# layout típico (nombre de mercado + línea, en líneas separadas o
# juntas); bookmakers con layouts muy distintos, texto rotado, o fotos
# borrosas de pantalla van a fallar total o parcialmente. Devuelve lo
# que pudo reconocer y lista aparte lo que no — no inventa una lectura
# cuando no está seguro. Upgrade path: swap por un modelo con visión
# real (Claude API) si esto no alcanza en la práctica.
"""
import re
import logging
from backend.pipeline.sofascore.equipos import buscar_candidatos

log = logging.getLogger(__name__)

_lector = None  # carga perezosa — EasyOCR tarda unos segundos en inicializar


def _get_lector():
    global _lector
    if _lector is None:
        import easyocr
        _lector = easyocr.Reader(["es", "en"], gpu=False)
    return _lector


# \s* (no \s+) — el OCR suele comerse espacios ("Más de" -> "Masde").
# Tampoco puede exigir tilde: "más"/"mas" varían según fuente/OCR.
_PATRON_OVER = re.compile(r"m[aá]s\s*de|over", re.I)
_PATRON_UNDER = re.compile(r"menos\s*de|under", re.I)
_PATRON_NUMERO = re.compile(r"(\d+[.,]\d+|\d+)")

_PALABRAS_CATEGORIA = {
    "gol": "goles", "goal": "goles",
    "corner": "corners", "córner": "corners", "esquina": "corners",
    "tarjeta": "tarjetas", "card": "tarjetas", "amarilla": "tarjetas",
}

# Substrings tolerantes a errores de OCR de 1-2 caracteres en
# "resultado del partido" — sin meterse en distancia de edición
# completa, alcanza con substrings robustos que sobreviven typos comunes
_FRAGMENTOS_RESULTADO = ("esultado", "resultad")


def _clasificar_over_under(texto: str) -> dict | None:
    numero = _PATRON_NUMERO.search(texto)
    if not numero:
        return None
    if _PATRON_OVER.search(texto):
        return {"lado": "over", "linea": float(numero.group(1).replace(",", "."))}
    if _PATRON_UNDER.search(texto):
        return {"lado": "under", "linea": float(numero.group(1).replace(",", "."))}
    return None


def _detectar_categoria(texto: str) -> str | None:
    texto_low = texto.lower()
    for palabra, categoria in _PALABRAS_CATEGORIA.items():
        if palabra in texto_low:
            return categoria
    return None


def _es_resultado_partido(texto: str) -> bool:
    t = texto.lower()
    return any(f in t for f in _FRAGMENTOS_RESULTADO) and "partido" in t


def _es_btts(texto: str) -> str | None:
    t = texto.lower()
    if "ambos equipos anotan" in t or "both teams to score" in t or "btts" in t:
        if "sí" in t or "si" in t or "yes" in t:
            return "si"
        if "no" in t:
            return "no"
    return None


def extraer_texto(ruta_imagen: str) -> list:
    return _get_lector().readtext(ruta_imagen, detail=0)


def analizar_captura_parley(db, ruta_imagen: str) -> dict:
    """{"equipos_detectados": [...], "selecciones": [...], "sin_reconocer": [...]}
    equipos_detectados: candidatos fuzzy-matcheados contra la tabla
    Equipo. selecciones: mercados que sí se pudieron clasificar
    (tipo="1x2"|"over_under"|"btts"). Nada se resuelve contra un partido
    real acá — eso lo hace el endpoint, que sabe con qué 2 equipos
    cruzar la búsqueda en Partido."""
    lineas = extraer_texto(ruta_imagen)

    equipos_candidatos = []
    selecciones = []
    sin_reconocer = []
    pendiente_over_under = None
    pendiente_resultado = None

    for linea in lineas:
        if _es_resultado_partido(linea):
            if pendiente_resultado:
                selecciones.append({"tipo": "1x2", "equipo_texto": pendiente_resultado})
                pendiente_resultado = None
            continue

        ou = _clasificar_over_under(linea)
        if ou:
            pendiente_over_under = ou
            continue

        if pendiente_over_under:
            categoria = _detectar_categoria(linea)
            if categoria:
                selecciones.append({"tipo": "over_under", "categoria": categoria, **pendiente_over_under})
                pendiente_over_under = None
                continue

        btts = _es_btts(linea)
        if btts:
            selecciones.append({"tipo": "btts", "seleccion": btts})
            continue

        candidatos = buscar_candidatos(db, linea, None, None)
        if candidatos and candidatos[0][1] is not None and candidatos[0][1] > 0.5:
            equipo, score = candidatos[0]
            # sin liga_id (la imagen no trae ese contexto) puede haber
            # más de un Equipo con el mismo nombre (bug real: dos filas
            # "Fluminense", id 124 y 20977, sin deduplicar en origen) —
            # se guardan TODOS los candidatos por encima del umbral, no
            # solo el top-1, para que resolver_partido_y_mercados pueda
            # desambiguar cruzando contra qué partido existe de verdad
            # (mismo principio que job_historico_sofascore._buscar_partido)
            equipos_candidatos.append({
                "texto_original": linea, "equipo_id": equipo.id,
                "equipo_ids": [e.id for e, s in candidatos if s is not None and s > 0.5],
                "nombre": equipo.nombre, "score": round(float(score), 3),
            })
            pendiente_resultado = linea
        else:
            sin_reconocer.append(linea)

    return {
        "lineas_ocr": lineas,
        "equipos_detectados": equipos_candidatos,
        "selecciones": selecciones,
        "sin_reconocer": sin_reconocer,
    }


def _linea_a_clave(linea: float) -> str:
    return str(linea).replace(".", "_").replace("-", "m")


VENTANA_DIAS_PARTIDO_ACTUAL = 3  # más lejos que esto de "hoy" -> probablemente
                                  # no es el partido de la imagen, no lo uses


def resolver_partido_y_mercados(db, analisis: dict):
    """A partir de lo que devolvió analizar_captura_parley(), busca el
    partido real (los 2 equipos detectados con más confianza) y traduce
    cada selección a la clave interna (mismo formato odds_* de siempre).
    Devuelve (partido, [{"mercado": clave, "nombre_legible": str}, ...], avisos).

    Un parley es casi siempre de un partido de HOY o de los próximos
    días — nunca "el partido más reciente entre estos equipos" a secas.
    Si el candidato más cercano a hoy queda a más de
    VENTANA_DIAS_PARTIDO_ACTUAL de distancia, casi seguro es de otra
    temporada — devolver ese análisis como si fuera el correcto sería
    peor que no responder nada (bug real: encontró Bodo/Glimt vs Union
    Saint-Gilloise de 2024 en vez del de 2026 que todavía no está en BD).
    """
    from backend.db.modelos import Partido
    from datetime import datetime

    avisos = []

    # de-duplica equipos por id, se queda con el mejor score de cada uno
    por_equipo = {}
    for e in analisis["equipos_detectados"]:
        actual = por_equipo.get(e["equipo_id"])
        if actual is None or e["score"] > actual["score"]:
            por_equipo[e["equipo_id"]] = e
    equipos = sorted(por_equipo.values(), key=lambda e: -e["score"])[:2]

    if len(equipos) < 2:
        avisos.append("No se reconocieron 2 equipos distintos en la imagen")
        return None, [], avisos

    ids_a = equipos[0].get("equipo_ids") or [equipos[0]["equipo_id"]]
    ids_b = equipos[1].get("equipo_ids") or [equipos[1]["equipo_id"]]
    candidatos = (
        db.query(Partido)
        .filter(
            ((Partido.equipo_local_id.in_(ids_a)) & (Partido.equipo_visit_id.in_(ids_b))) |
            ((Partido.equipo_local_id.in_(ids_b)) & (Partido.equipo_visit_id.in_(ids_a)))
        )
        .all()
    )
    if not candidatos:
        avisos.append(f"No hay ningún partido en BD entre {equipos[0]['nombre']} y {equipos[1]['nombre']}")
        return None, [], avisos

    ahora = datetime.now()
    partido = min(candidatos, key=lambda p: abs((p.fecha - ahora).total_seconds()))
    dias_diferencia = abs((partido.fecha - ahora).days)

    if dias_diferencia > VENTANA_DIAS_PARTIDO_ACTUAL:
        avisos.append(
            f"Hay un partido entre {equipos[0]['nombre']} y {equipos[1]['nombre']} en BD, "
            f"pero es del {partido.fecha.date()} ({dias_diferencia} días de hoy) — "
            f"probablemente NO es el de la imagen. El partido actual entre estos equipos "
            f"todavía no está cargado (típico en fases clasificatorias de copas europeas, "
            f"cobertura incompleta ahí)."
        )
        return None, [], avisos

    mercados = []
    for sel in analisis["selecciones"]:
        if sel["tipo"] == "1x2":
            candidatos = [e for e in equipos if e["texto_original"] == sel["equipo_texto"]]
            if not candidatos:
                avisos.append(f"No se pudo ligar la selección 1X2 a un equipo detectado: {sel['equipo_texto']!r}")
                continue
            # contra la lista de candidatos (no un id único ya fijado) —
            # mismo motivo que arriba: puede haber más de un Equipo con
            # ese nombre, el que importa es el que realmente juega HOY
            ids_candidatos = candidatos[0].get("equipo_ids") or [candidatos[0]["equipo_id"]]
            if partido.equipo_local_id in ids_candidatos:
                clave = "local"
            elif partido.equipo_visit_id in ids_candidatos:
                clave = "visitante"
            else:
                continue
            mercados.append({"mercado": clave, "nombre_legible": f"1X2 {clave.capitalize()}"})

        elif sel["tipo"] == "over_under":
            clave = f"{sel['categoria']}_{sel['lado']}_{_linea_a_clave(sel['linea'])}"
            mercados.append({
                "mercado": clave,
                "nombre_legible": f"{sel['categoria'].capitalize()} {sel['lado'].capitalize()} {sel['linea']}",
            })

        elif sel["tipo"] == "btts":
            clave = f"btts_{sel['seleccion']}"
            mercados.append({"mercado": clave, "nombre_legible": f"BTTS {'Sí' if sel['seleccion']=='si' else 'No'}"})

    return partido, mercados, avisos
