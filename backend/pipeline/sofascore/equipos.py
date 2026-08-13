"""Resolución de equipos/liga por nombre de Sofascore contra la BD propia.

Compartido por job_historico_sofascore.py, job_sofascore.py (diario) y
el loader de fixtures nuevos — un solo lugar para la heurística de match.
"""
from sqlalchemy import func, or_
from backend.db.modelos import Equipo, Liga, Partido

# Umbrales de match de nombre de equipo (pg_trgm).
# Ningún umbral único separa positivos de negativos: "Rennes" vs
# "Stade Rennais" da 0.571 y el falso "Al-Fayha" vs "Al-Fateh" da 0.556.
# Lo que sí resuelve es el ORDER BY: el equipo correcto saca ~1.0 y gana.
UMBRAL_SIMILITUD = 0.35   # mínimo para USAR el match en esta búsqueda
UMBRAL_ANCLAJE   = 0.7    # mínimo para PERSISTIR el sofascore_id
# Anclar de más es peor que no anclar: un sofascore_id equivocado hace que
# el lookup exacto corte antes de la similitud y congela el error para
# siempre. Un match flojo se usa hoy y se vuelve a calcular la próxima.

# Sofascore separa algunas ligas en Apertura/Clausura; nuestra BD las
# guarda todas bajo un solo nombre de liga.
ALIAS_LIGA = {
    "Liga MX Apertura": "Liga MX",
    "Liga MX Clausura": "Liga MX",
}


def resolver_liga_id(db, nombre_liga: str) -> int | None:
    """id en NUESTRA BD de una liga por nombre (distinto del id de
    Sofascore usado para las llamadas a la API — numeraciones separadas
    que comparten el mismo nombre)."""
    nombre_bd = ALIAS_LIGA.get(nombre_liga, nombre_liga)
    liga = db.query(Liga).filter(Liga.nombre == nombre_bd).first()
    return liga.id if liga else None


def equipos_de_la_liga(db, liga_id: int | None):
    """Query base de equipos, acotada a los que ya jugaron en esta liga
    (evita que la heurística por nombre cruce ligas — "América" no debe
    matchear Club America (Liga MX) y America Mineiro (Brasileirao) a la
    vez). Sin liga_id cae a búsqueda sin acotar."""
    q = db.query(Equipo)
    if liga_id:
        q = q.join(
            Partido,
            or_(Partido.equipo_local_id == Equipo.id,
                Partido.equipo_visit_id == Equipo.id)
        ).filter(Partido.liga_id == liga_id)
    return q


def buscar_candidatos(db, nombre: str, sofascore_team_id, liga_id: int | None):
    """Devuelve [(Equipo, score), ...]. score=None si vino de un
    sofascore_id ya anclado (match exacto, sin ambigüedad posible).

    Puede haber empate real ("Athletico" mide igual contra Atletico
    Paranaense, Atletico-MG y Atletico Goianiense — nombre corto, tres
    clubes brasileños empiezan igual). Elegir uno acá sería arbitrario,
    así que se devuelven TODOS los candidatos por encima del umbral y se
    deja que el llamador desambigüe con más contexto (rival + fecha)."""
    if sofascore_team_id:
        equipo = (
            db.query(Equipo)
            .filter(Equipo.sofascore_id == sofascore_team_id)
            .first()
        )
        if equipo:
            return [(equipo, None)]

    # similarity() compara los nombres enteros; word_similarity() busca el
    # mejor tramo de palabras, que es lo que resuelve nombre corto vs largo
    # ("Lyon" dentro de "Olympique Lyonnais"). Se toma el mayor de las tres
    # medidas — word_similarity es asimétrica, así que va en ambos sentidos.
    db_nom = func.unaccent(Equipo.nombre)
    ss_nom = func.unaccent(nombre)
    score = func.greatest(
        func.similarity(db_nom, ss_nom),
        func.word_similarity(db_nom, ss_nom),
        func.word_similarity(ss_nom, db_nom),
    )
    candidatos = (
        equipos_de_la_liga(db, liga_id)
        .add_columns(score.label("score"))
        .filter(score > UMBRAL_SIMILITUD)
        .order_by(score.desc())
        .all()
    )
    if candidatos:
        return candidatos

    # Sin candidatos EN ESA LIGA, se busca en todas. Un club existe una
    # sola vez aunque juegue varios torneos, y limitar la búsqueda a la
    # liga que se está importando crea duplicados: Mirassol ya estaba
    # cargado (había entrado por Copa Libertadores) y al importar
    # Brasileirao 2026 no se lo encontró, así que se creó una segunda
    # fila. Resultado: el partido de Libertadores apuntaba a la fila sin
    # historial y el modelo lo descartaba por "historial insuficiente",
    # mientras los 58 partidos estaban colgados de la otra.
    return (
        db.query(Equipo)
        .add_columns(score.label("score"))
        .filter(score > UMBRAL_SIMILITUD)
        .order_by(score.desc())
        .limit(5)
        .all()
    )


def anclar_si_corresponde(db, candidatos, equipo_id_correcto, sofascore_team_id):
    """Una vez confirmado (por cruce con Partido: rival+fecha) cuál
    candidato era el correcto, ancla su sofascore_id — solo si el match
    individual era lo bastante confiable como para persistir."""
    if not sofascore_team_id:
        return
    for equipo, score in candidatos:
        if equipo.id != equipo_id_correcto:
            continue
        if not equipo.sofascore_id and (score is None or score >= UMBRAL_ANCLAJE):
            equipo.sofascore_id = sofascore_team_id
            db.commit()
        break
