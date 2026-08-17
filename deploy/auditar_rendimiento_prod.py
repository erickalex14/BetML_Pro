"""Auditoría read-only de recomendaciones cerradas en producción."""
import argparse
import ast
import csv
import io
import json
import math
import os
from collections import defaultdict
from datetime import datetime, timedelta

import paramiko


def _consultar(cliente, sql: str) -> list[dict]:
    comando = (
        "docker exec -i betml-db sh -c "
        "'psql -U \"$POSTGRES_USER\" -d \"$POSTGRES_DB\" --csv -P footer=off'"
    )
    entrada, salida, error = cliente.exec_command(comando)
    entrada.write(sql)
    entrada.flush()
    entrada.channel.shutdown_write()
    texto = salida.read().decode("utf-8", errors="replace")
    fallo = error.read().decode("utf-8", errors="replace")
    codigo = salida.channel.recv_exit_status()
    if codigo:
        raise RuntimeError(fallo or texto)
    if not texto.strip():
        raise RuntimeError(f"Consulta sin salida. stderr={fallo!r}")
    return list(csv.DictReader(io.StringIO(texto)))


def _comando(cliente, comando: str) -> str:
    _, salida, error = cliente.exec_command(comando)
    texto = salida.read().decode("utf-8", errors="replace")
    fallo = error.read().decode("utf-8", errors="replace")
    if salida.channel.recv_exit_status():
        raise RuntimeError(fallo or texto)
    return texto.strip()


def _familia(mercado: str) -> str:
    for prefijo, familia in (
        ("corners", "córners"), ("tarjetas", "tarjetas"),
        ("rojas", "rojas"), ("goles_equipo", "goles_equipo"),
        ("goles_1t", "goles_1t"), ("goles", "goles"),
        ("btts", "btts"), ("handicap", "hándicap"),
        ("1t_", "resultado_1t"), ("2t_", "resultado_2t"),
        ("jugador_", "jugadores"),
    ):
        if mercado.startswith(prefijo):
            return familia
    return "1x2" if mercado in {"local", "empate", "visitante"} else "otros"


def _wilson(aciertos: int, n: int) -> list[float] | None:
    if not n:
        return None
    z = 1.96
    p = aciertos / n
    den = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / den
    margen = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / den
    return [round(centro - margen, 4), round(centro + margen, 4)]


def _resumen(filas: list[dict]) -> dict:
    cerradas = [f for f in filas if f["acerto"] in {"t", "f"}]
    aciertos = sum(f["acerto"] == "t" for f in cerradas)
    probs = [float(f["probabilidad"]) for f in cerradas]
    con_cuota = [f for f in cerradas if f["cuota"]]
    ganancias = [
        (float(f["cuota"]) - 1) if f["acerto"] == "t" else -1
        for f in con_cuota
    ]
    return {
        "n": len(cerradas),
        "aciertos": aciertos,
        "accuracy": round(aciertos / len(cerradas), 4) if cerradas else None,
        "ic95_accuracy": _wilson(aciertos, len(cerradas)),
        "probabilidad_media": round(sum(probs) / len(probs), 4) if probs else None,
        "brecha_calibracion": round(aciertos / len(cerradas) - sum(probs) / len(probs), 4)
        if probs else None,
        "brier": round(sum((float(f["probabilidad"]) - (f["acerto"] == "t")) ** 2
                           for f in cerradas) / len(cerradas), 4) if cerradas else None,
        "n_con_cuota": len(con_cuota),
        "roi_plano": round(sum(ganancias) / len(ganancias), 4) if ganancias else None,
    }


def _agrupar(filas: list[dict], clave) -> dict:
    grupos = defaultdict(list)
    for fila in filas:
        grupos[clave(fila)].append(fila)
    return {k: _resumen(v) for k, v in sorted(grupos.items())}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--desde", required=True, help="YYYY-MM-DD, hora Ecuador")
    parser.add_argument("--hasta", required=True, help="YYYY-MM-DD exclusivo, hora Ecuador")
    args = parser.parse_args()
    desde = datetime.fromisoformat(args.desde) + timedelta(hours=5)
    hasta = datetime.fromisoformat(args.hasta) + timedelta(hours=5)

    host = os.environ["BETML_SSH_HOST"]
    cliente = paramiko.SSHClient()
    cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cliente.connect(
        host,
        port=int(os.environ.get("BETML_SSH_PORT", "22")),
        username=os.environ["BETML_SSH_USER"],
        password=os.environ["BETML_SSH_PASS"],
        timeout=20,
    )
    try:
        calidad = _consultar(cliente, f"""
select count(*) as partidos,
       count(*) filter (where estado='FT') as terminados,
       count(*) filter (where estado='FT' and goles_local is not null and goles_visitante is not null) as marcador_completo,
       count(*) filter (where estado='FT' and exists(select 1 from estadisticas_sofascores s where s.partido_id=partidos.id)) as stats_sofascore
from partidos where fecha >= timestamp '{desde}' and fecha < timestamp '{hasta}';
""")[0]
        filas = _consultar(cliente, f"""
select distinct on (p.partido_id,p.mercado)
       p.id,p.partido_id,p.mercado,p.prediccion,p.probabilidad,p.acerto,
       p.creado_en,pa.fecha,pa.estado,l.nombre as liga,o.cuota,
       el.nombre as local,ev.nombre as visitante,pa.goles_local,pa.goles_visitante
from predicciones p
join partidos pa on pa.id=p.partido_id
join ligas l on l.id=pa.liga_id
join equipos el on el.id=pa.equipo_local_id
join equipos ev on ev.id=pa.equipo_visit_id
left join lateral (
  select max(valor) as cuota from odds
  where partido_id=p.partido_id and mercado='odds_' || p.mercado
) o on true
where p.usuario_id is null
  and p.mercado not like '1X2-%'
  and pa.fecha >= timestamp '{desde}' and pa.fecha < timestamp '{hasta}'
order by p.partido_id,p.mercado,p.creado_en asc;
""")
        modelos_1x2 = _consultar(cliente, f"""
select distinct on (p.partido_id,p.mercado)
       p.id,p.partido_id,p.mercado,p.prediccion,p.probabilidad,p.acerto,
       p.creado_en,pa.fecha,pa.estado,l.nombre as liga,o.cuota
from predicciones p
join partidos pa on pa.id=p.partido_id
join ligas l on l.id=pa.liga_id
left join lateral (
  select max(valor) as cuota from odds
  where partido_id=p.partido_id
    and mercado='odds_' || case lower(p.prediccion)
      when 'local' then 'local' when 'empate' then 'empate' when 'visitante' then 'visitante' end
) o on true
where p.usuario_id is null and p.mercado like '1X2-%'
  and pa.fecha >= timestamp '{desde}' and pa.fecha < timestamp '{hasta}'
order by p.partido_id,p.mercado,p.creado_en asc;
""")
        duplicados = _consultar(cliente, f"""
select count(*) as grupos,coalesce(sum(n-1),0) as extras from (
  select p.partido_id,p.mercado,count(*) n
  from predicciones p join partidos pa on pa.id=p.partido_id
  where p.usuario_id is null and p.mercado not like '1X2-%'
    and pa.fecha >= timestamp '{desde}' and pa.fecha < timestamp '{hasta}'
  group by 1,2 having count(*)>1
) d;
""")[0]
        calibracion = ast.literal_eval(_comando(
            cliente,
            "docker exec betml-api python -c 'from backend.models.calibracion_produccion import cargar; print(cargar())'",
        ))
        logs = _comando(
            cliente,
            "docker logs --since 72h betml-scheduler 2>&1 | "
            "grep -E 'Reentrenamiento|Calibraci|recomendadas|Cerrar Predicciones|ERROR|Error' | tail -120",
        )
    finally:
        cliente.close()

    justas = [f for f in filas if datetime.fromisoformat(f["creado_en"]) <= datetime.fromisoformat(f["fecha"])]
    modelos_1x2_justos = [f for f in modelos_1x2
                          if datetime.fromisoformat(f["creado_en"]) <= datetime.fromisoformat(f["fecha"])]
    fijas = [f for f in justas if float(f["probabilidad"]) >= 0.55]
    salida = {
        "ventana_ecuador": {"desde": args.desde, "hasta_exclusivo": args.hasta},
        "calidad": {
            **{k: int(v) for k, v in calidad.items()},
            "recomendaciones_unicas": len(filas),
            "creadas_antes_inicio": len(justas),
            "creadas_despues_inicio": len(filas) - len(justas),
            "duplicados": {k: int(v) for k, v in duplicados.items()},
            "pendientes": sum(f["acerto"] not in {"t", "f"} for f in justas),
        },
        "todas": _resumen(justas),
        "fijas_prob_55": _resumen(fijas),
        "modelos_1x2": {
            "todos": _resumen(modelos_1x2_justos),
            "por_modelo": _agrupar(modelos_1x2_justos, lambda f: f["mercado"]),
        },
        "por_familia": _agrupar(justas, lambda f: _familia(f["mercado"])),
        "por_mercado": _agrupar(justas, lambda f: f["mercado"]),
        "por_liga": _agrupar(justas, lambda f: f["liga"]),
        "por_bucket_prob": _agrupar(
            justas,
            lambda f: f"{int(float(f['probabilidad']) * 10) * 10:02d}-{int(float(f['probabilidad']) * 10) * 10 + 9:02d}%",
        ),
        "fallos_mayor_confianza": [
            {k: f[k] for k in ("partido_id", "local", "visitante", "liga", "mercado",
                                "probabilidad", "cuota", "goles_local", "goles_visitante")}
            for f in sorted((x for x in justas if x["acerto"] == "f"),
                            key=lambda x: float(x["probabilidad"]), reverse=True)[:15]
        ],
        "calibracion_cargada": calibracion,
        "logs_scheduler_filtrados": logs.splitlines(),
    }
    print(json.dumps(salida, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
