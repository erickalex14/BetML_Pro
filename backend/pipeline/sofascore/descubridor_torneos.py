"""Encuentra el id de torneo de Sofascore de una liga nuestra cuando
LIGAS_SOFASCORE no lo tiene mapeado — fases de clasificación (que viven
bajo OTRO unique-tournament id que la fase principal) y los amistosos
(repartidos en varios torneos, no solo "Club Friendly Games").

Cómo: /sport/football/scheduled-tournaments/{fecha}/page/{n} lista TODOS
los torneos con partidos ese día (endpoint sacado del tráfico real de
sofascore.com). Son cientos por día, así que NO se piden los eventos de
todos — se filtran candidatos por parecido de nombre con la liga nuestra
y recién ahí se piden los eventos de esos pocos.

Lo que aprende se guarda en LigaSofascoreTorneo, así el descubrimiento
se paga una sola vez por liga y no en cada corrida (el job corre cada 15
min; re-descubrir siempre sería pegarle a Sofascore al pedo y arriesgar
el anti-bot).
"""
import logging
import unicodedata

log = logging.getLogger(__name__)

MAX_PAGINAS = 3          # ~300 torneos/día, de sobra
MAX_CANDIDATOS = 8       # tope de torneos a los que pedirles eventos
_LARGO_RAIZ = 6          # "friendl" pega con "friendly" y "friendlies"

# Palabras que no distinguen nada — están en media docena de torneos
_GENERICAS = {
    "liga", "league", "copa", "cup", "clubs", "club", "division", "primera",
    "football", "futbol", "campeonato", "torneo", "trophy", "super",
}


def _tokens(nombre: str) -> set:
    sin_acentos = unicodedata.normalize("NFKD", nombre)
    sin_acentos = "".join(c for c in sin_acentos if not unicodedata.combining(c))
    limpio = "".join(c if c.isalnum() else " " for c in sin_acentos.lower())
    return {t for t in limpio.split() if len(t) >= 4 and t not in _GENERICAS}


def _parecido(nombre_liga: str, nombre_torneo: str) -> bool:
    """True si comparten alguna palabra significativa (por raíz, para que
    'Friendlies' pegue con 'Friendly')."""
    raices_liga = {t[:_LARGO_RAIZ] for t in _tokens(nombre_liga)}
    raices_torneo = {t[:_LARGO_RAIZ] for t in _tokens(nombre_torneo)}
    return bool(raices_liga & raices_torneo)


def torneos_conocidos(db, liga_id: int) -> list:
    """Ids de torneo ya aprendidos para esta liga."""
    from backend.db.modelos import LigaSofascoreTorneo
    filas = (db.query(LigaSofascoreTorneo)
             .filter(LigaSofascoreTorneo.liga_id == liga_id)
             .all())
    return [f.sofascore_torneo_id for f in filas]


def recordar_torneo(db, liga_id: int, torneo_id: int, nombre_sofascore: str) -> None:
    from backend.db.modelos import LigaSofascoreTorneo
    ya = db.get(LigaSofascoreTorneo, (liga_id, torneo_id))
    if ya is not None:
        return
    db.add(LigaSofascoreTorneo(liga_id=liga_id, sofascore_torneo_id=torneo_id,
                               nombre_sofascore=nombre_sofascore))
    db.commit()
    log.info(f"Torneo aprendido — liga {liga_id} → Sofascore {torneo_id} ({nombre_sofascore!r})")


def torneos_del_dia(cliente, fecha: str) -> list:
    """[(torneo_id, nombre)] de TODOS los torneos con partidos ese día.

    La lista es la misma para todas nuestras ligas — se pide una vez por
    fecha y se filtra en memoria (antes se pedían las 3 páginas por cada
    liga pendiente, multiplicando requests al pedo justo contra el
    servicio que no queremos saturar)."""
    torneos, vistos = [], set()
    for pagina in range(1, MAX_PAGINAS + 1):
        data = cliente.get(f"/sport/football/scheduled-tournaments/{fecha}/page/{pagina}")
        if not data:
            break
        for entrada in data.get("scheduled", []):
            unico = (entrada.get("tournament") or {}).get("uniqueTournament") or {}
            torneo_id, nombre = unico.get("id"), unico.get("name", "")
            if torneo_id and nombre and torneo_id not in vistos:
                vistos.add(torneo_id)
                torneos.append((torneo_id, nombre))
        if not data.get("hasNextPage"):
            break
    return torneos


def filtrar_candidatos(torneos: list, nombre_liga: str) -> list:
    """De la lista del día, los que se parecen por nombre a nuestra liga.
    Sin coincidencias devuelve [] — mejor nada que pedirle los eventos a
    300 torneos."""
    candidatos = [(tid, nombre) for tid, nombre in torneos if _parecido(nombre_liga, nombre)]
    if len(candidatos) > MAX_CANDIDATOS:
        log.info(f"'{nombre_liga}': {len(candidatos)} candidatos, se prueban los primeros {MAX_CANDIDATOS}")
    return candidatos[:MAX_CANDIDATOS]
