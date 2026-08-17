"""Construcción del grafo equipo-jugador para la GNN.

Dos tipos de nodo (equipo, jugador), dos tipos de arista:
  - (equipo, jugo_contra, equipo): partidos históricos, arista ponderada
    por diferencia de gol (positivo = local ganó, útil como feature de
    arista, no solo conectividad).
  - (jugador, juega_en, equipo): pertenencia — de qué equipo es cada
    jugador, derivada de partido.equipo_local_id/equipo_visit_id +
    estadisticas_jugador.es_local (la columna equipo_id de
    estadisticas_jugador está 100% vacía en los datos reales, nunca se
    pobló — no es una opción usarla directo).

LIMITACIÓN CONOCIDA: dentro del bloque de entrenamiento se usa una sola
foto del grafo en vez de reconstruirla por partido. La validación sí es
temporalmente segura: entrenar_gnn() congela esta foto antes de la fecha
de corte y no introduce aristas ni resultados del bloque reservado.
Un backtest walk-forward con snapshots periódicos sería el siguiente
nivel de rigor, pero ya no contamina la métrica publicada.
"""
import logging
import numpy as np
import torch
from sqlalchemy import text
from torch_geometric.data import HeteroData

log = logging.getLogger(__name__)

N_FEATURES_EQUIPO = 6   # win_rate, gf_prom, gc_prom, xg_favor_prom, xg_contra_prom, n_partidos (log)
N_FEATURES_JUGADOR = 6  # tiros_prom, tiros_arco_prom, goles_prom, rating_prom, prob_amarilla, n_partidos (log)


def construir_grafo(db, fecha_corte=None) -> tuple[HeteroData, dict, dict]:
    """Devuelve (grafo, id_a_indice_equipo, id_a_indice_jugador).
    fecha_corte=None usa todo el histórico disponible (career-to-date)."""
    filtro_fecha = "and p.fecha < :fecha_corte" if fecha_corte else ""
    params = {"fecha_corte": fecha_corte} if fecha_corte else {}

    # ── Features de equipo (agregado, una query) ────────────────────
    filas_equipo = db.execute(text(f"""
        select equipo_id,
               count(*) as n_partidos,
               avg(gano::int) as win_rate,
               avg(gf) as gf_prom,
               avg(gc) as gc_prom,
               avg(xg_favor) as xg_favor_prom,
               avg(xg_contra) as xg_contra_prom
        from (
            select p.equipo_local_id as equipo_id,
                   (p.goles_local > p.goles_visitante) as gano,
                   p.goles_local as gf, p.goles_visitante as gc,
                   e.xg_local as xg_favor, e.xg_visitante as xg_contra
            from partidos p left join estadisticas_sofascores e on e.partido_id = p.id
            where p.estado = 'FT' and p.goles_local is not null {filtro_fecha}
            union all
            select p.equipo_visit_id,
                   (p.goles_visitante > p.goles_local),
                   p.goles_visitante, p.goles_local,
                   e.xg_visitante, e.xg_local
            from partidos p left join estadisticas_sofascores e on e.partido_id = p.id
            where p.estado = 'FT' and p.goles_local is not null {filtro_fecha}
        ) t
        group by equipo_id
    """), params).fetchall()

    equipo_ids = [f.equipo_id for f in filas_equipo]
    idx_equipo = {eid: i for i, eid in enumerate(equipo_ids)}

    x_equipo = np.zeros((len(equipo_ids), N_FEATURES_EQUIPO), dtype=np.float32)
    for i, f in enumerate(filas_equipo):
        x_equipo[i] = [
            f.win_rate or 0.0,
            f.gf_prom or 0.0,
            f.gc_prom or 0.0,
            f.xg_favor_prom or 0.0,
            f.xg_contra_prom or 0.0,
            np.log1p(f.n_partidos),
        ]

    # ── Features de jugador (agregado, una query) ───────────────────
    # equipo_id de estadisticas_jugador está siempre vacío — el equipo
    # real sale de es_local + el partido (mismo patrón que todo el resto
    # del proyecto usa para evitar ese hueco de datos).
    filas_jugador = db.execute(text(f"""
        select ej.sofascore_jugador_id,
               count(*) as n_partidos,
               avg(coalesce(ej.tiros, 0)) as tiros_prom,
               avg(coalesce(ej.tiros_arco, 0)) as tiros_arco_prom,
               avg(coalesce(ej.goles, 0)) as goles_prom,
               avg(ej.rating) as rating_prom,
               avg(ej.amarilla::int) as prob_amarilla
        from estadisticas_jugador ej
        join partidos p on p.id = ej.partido_id
        where p.estado = 'FT' {filtro_fecha}
        group by ej.sofascore_jugador_id
        having count(*) >= 3
    """), params).fetchall()

    jugador_ids = [f.sofascore_jugador_id for f in filas_jugador]
    idx_jugador = {jid: i for i, jid in enumerate(jugador_ids)}

    x_jugador = np.zeros((len(jugador_ids), N_FEATURES_JUGADOR), dtype=np.float32)
    for i, f in enumerate(filas_jugador):
        x_jugador[i] = [
            f.tiros_prom or 0.0,
            f.tiros_arco_prom or 0.0,
            f.goles_prom or 0.0,
            f.rating_prom or 6.5,
            f.prob_amarilla or 0.0,
            np.log1p(f.n_partidos),
        ]

    # ── Aristas equipo-equipo (cada partido, ambas direcciones) ─────
    filas_partidos = db.execute(text(f"""
        select equipo_local_id, equipo_visit_id, goles_local, goles_visitante
        from partidos p
        where estado = 'FT' and goles_local is not null {filtro_fecha}
    """), params).fetchall()

    src_ee, dst_ee, peso_ee = [], [], []
    for f in filas_partidos:
        if f.equipo_local_id not in idx_equipo or f.equipo_visit_id not in idx_equipo:
            continue
        dif = (f.goles_local or 0) - (f.goles_visitante or 0)
        src_ee += [idx_equipo[f.equipo_local_id], idx_equipo[f.equipo_visit_id]]
        dst_ee += [idx_equipo[f.equipo_visit_id], idx_equipo[f.equipo_local_id]]
        peso_ee += [float(dif), float(-dif)]

    # ── Aristas jugador-equipo (última asociación conocida) ─────────
    filas_roster = db.execute(text(f"""
        select distinct ej.sofascore_jugador_id,
               case when ej.es_local then p.equipo_local_id else p.equipo_visit_id end as equipo_id
        from estadisticas_jugador ej
        join partidos p on p.id = ej.partido_id
        where p.estado = 'FT' {filtro_fecha}
    """), params).fetchall()

    src_je, dst_je = [], []
    for f in filas_roster:
        if f.sofascore_jugador_id not in idx_jugador or f.equipo_id not in idx_equipo:
            continue
        src_je.append(idx_jugador[f.sofascore_jugador_id])
        dst_je.append(idx_equipo[f.equipo_id])

    grafo = HeteroData()
    grafo["equipo"].x = torch.tensor(x_equipo, dtype=torch.float32)
    grafo["jugador"].x = torch.tensor(x_jugador, dtype=torch.float32)

    grafo["equipo", "jugo_contra", "equipo"].edge_index = torch.tensor(
        [src_ee, dst_ee], dtype=torch.long) if src_ee else torch.zeros((2, 0), dtype=torch.long)
    grafo["equipo", "jugo_contra", "equipo"].edge_attr = torch.tensor(
        peso_ee, dtype=torch.float32).unsqueeze(-1) if peso_ee else torch.zeros((0, 1), dtype=torch.float32)

    grafo["jugador", "juega_en", "equipo"].edge_index = torch.tensor(
        [src_je, dst_je], dtype=torch.long) if src_je else torch.zeros((2, 0), dtype=torch.long)
    grafo["equipo", "rev_juega_en", "jugador"].edge_index = torch.tensor(
        [dst_je, src_je], dtype=torch.long) if src_je else torch.zeros((2, 0), dtype=torch.long)

    log.info(f"Grafo: {len(equipo_ids)} equipos, {len(jugador_ids)} jugadores, "
             f"{len(src_ee)} aristas equipo-equipo, {len(src_je)} aristas jugador-equipo")

    return grafo, idx_equipo, idx_jugador
