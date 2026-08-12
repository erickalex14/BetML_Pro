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
    asistencias = np.random.poisson(lam=max(forma["asistencias_prom"], 0.01), size=n_simulaciones)
    pases = np.random.poisson(lam=max(forma["pases_prom"], 0.01), size=n_simulaciones)
    duelos = np.random.poisson(lam=max(forma["duelos_prom"], 0.01), size=n_simulaciones)
    # Solo tiene sentido para arqueros — jugadores de campo dan atajadas_prom≈0
    # (Sofascore no les registra el stat), el Poisson resultante ya sale
    # ~0 solo, no hace falta filtrar acá por posición.
    atajadas = np.random.poisson(lam=max(forma["atajadas_prom"], 0.01), size=n_simulaciones)

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
        "asistencias": {
            "promedio": round(float(np.mean(asistencias)), 2),
            "over_under": over_under(asistencias, [0.5]),
        },
        "pases": {
            "promedio": round(float(np.mean(pases)), 2),
            "over_under": over_under(pases, [20.5, 30.5, 40.5]),
        },
        "entradas": {
            "promedio": round(float(np.mean(duelos)), 2),
            "over_under": over_under(duelos, [1.5, 2.5, 3.5]),
        },
        "atajadas": {
            "promedio": round(float(np.mean(atajadas)), 2),
            "over_under": over_under(atajadas, [1.5, 2.5, 3.5, 4.5]),
        },
        "goles": {
            "promedio": round(float(np.mean(goles)), 2),
            "over_under": over_under(goles, [0.5, 1.5]),  # anota / anota 2+
        },
        "prob_anota": round(float(np.mean(goles >= 1)), 4),
        "prob_amarilla": round(forma["prob_amarilla"], 4),
        "prob_roja": round(forma["prob_roja"], 4),
    }


def simular_jugadores_partido(db, partido, n_simulaciones: int = 10000) -> dict:
    """Simula mercados individuales para el XI de ambos equipos. Usa la
    alineación CONFIRMADA por Sofascore si job_alineaciones.py ya la trajo
    (real, no puede listar a alguien que ya se fue del club); si todavía
    no salió (falta más de ~90 min para el partido), cae al heurístico de
    "quién jugó de titular más seguido últimamente" — ver
    obtener_titulares_probables().
    Devuelve {"local": [...], "visitante": [...]}, cada elemento con
    nombre/posición + su simulación. Jugadores sin historial suficiente
    (fichajes recientes, debuts) se omiten — no hay con qué estimarlos."""
    from backend.features.jugadores import (
        obtener_lineup_confirmada, obtener_titulares_probables, calcular_forma_jugador)

    resultado = {"local": [], "visitante": []}

    for lado, equipo_id, es_local in (
        ("local", partido.equipo_local_id, True),
        ("visitante", partido.equipo_visit_id, False),
    ):
        probables = (obtener_lineup_confirmada(db, partido.id, es_local)
                     or obtener_titulares_probables(db, equipo_id, partido.fecha, es_local))
        for jugador in probables:
            forma = calcular_forma_jugador(db, jugador["sofascore_jugador_id"], partido.fecha)
            if forma is None:
                continue
            sim = simular_jugador(forma, n_simulaciones)
            resultado[lado].append({**jugador, **sim})

    return resultado
