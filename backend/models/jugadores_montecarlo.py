"""Simulación Monte Carlo de mercados individuales de jugador — tiros,
tiros al arco, anotar (anytime goalscorer), amarilla, roja.

Poisson independiente por jugador con λ = su propio promedio histórico
(calcular_forma_jugador). Sin corrección tipo Dixon-Coles — esa
correlación es específica del marcador entre dos equipos, no hay
evidencia de que aplique entre las stats individuales de un jugador.

Amarilla/roja son eventos binarios raros (una 2da amarilla ES la roja
en los datos, no dos amarillas separadas) — se usa la tasa empírica
directa en vez de Poisson, que no tiene sentido para un evento que como
mucho pasa una vez por partido.
"""
import logging
import numpy as np

log = logging.getLogger(__name__)


def simular_jugador(forma: dict, n_simulaciones: int = 10000,
                     seed: int = 42) -> dict:
    if seed is not None:
        np.random.seed(seed)

    tiros = np.random.poisson(lam=max(forma["tiros_prom"], 0.01), size=n_simulaciones)
    # Tiros al arco nunca puede superar tiros totales del jugador en esa
    # simulación — se cappea, no son dos Poisson independientes.
    tiros_arco_raw = np.random.poisson(lam=max(forma["tiros_arco_prom"], 0.01), size=n_simulaciones)
    tiros_arco = np.minimum(tiros_arco_raw, tiros)

    goles = np.random.poisson(lam=max(forma["goles_prom"], 0.01), size=n_simulaciones)

    def over_under(arr, lineas):
        return {
            f"over_{str(l).replace('.', '_')}": round(float(np.mean(arr > l)), 4)
            for l in lineas
        }

    return {
        "n_partidos_historial": forma["n_partidos"],
        "tiros": {
            "promedio": round(float(np.mean(tiros)), 2),
            "over_under": over_under(tiros, [0.5, 1.5, 2.5]),
        },
        "tiros_arco": {
            "promedio": round(float(np.mean(tiros_arco)), 2),
            "over_under": over_under(tiros_arco, [0.5, 1.5]),
        },
        "prob_anota": round(float(np.mean(goles >= 1)), 4),
        "prob_amarilla": round(forma["prob_amarilla"], 4),
        "prob_roja": round(forma["prob_roja"], 4),
    }


def simular_jugadores_partido(db, partido, n_simulaciones: int = 10000) -> dict:
    """Simula mercados individuales para el XI probable de ambos equipos.
    Devuelve {"local": [...], "visitante": [...]}, cada elemento con
    nombre/posición + su simulación. Jugadores sin historial suficiente
    (fichajes recientes, debuts) se omiten — no hay con qué estimarlos."""
    from backend.features.jugadores import obtener_titulares_probables, calcular_forma_jugador

    resultado = {"local": [], "visitante": []}

    for lado, equipo_id, es_local in (
        ("local", partido.equipo_local_id, True),
        ("visitante", partido.equipo_visit_id, False),
    ):
        probables = obtener_titulares_probables(db, equipo_id, partido.fecha, es_local)
        for jugador in probables:
            forma = calcular_forma_jugador(db, jugador["sofascore_jugador_id"], partido.fecha)
            if forma is None:
                continue
            sim = simular_jugador(forma, n_simulaciones)
            resultado[lado].append({**jugador, **sim})

    return resultado
