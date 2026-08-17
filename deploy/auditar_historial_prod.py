"""Auditoria de solo lectura del historial real de un equipo en produccion."""
import os
import shlex
import sys

import paramiko


def main() -> None:
    termino = (sys.argv[1] if len(sys.argv) > 1 else "Al Hilal").replace("'", "''")
    if termino == "--coverage":
        sql = """
        WITH proximos AS (
          SELECT p.*,
            (SELECT count(*) FROM partidos h WHERE h.estado='FT' AND h.fecha<p.fecha
              AND h.liga_id NOT IN (10,667) AND
              (h.equipo_local_id=p.equipo_local_id OR h.equipo_visit_id=p.equipo_local_id)) hl,
            (SELECT count(*) FROM partidos h WHERE h.estado='FT' AND h.fecha<p.fecha
              AND h.liga_id NOT IN (10,667) AND
              (h.equipo_local_id=p.equipo_visit_id OR h.equipo_visit_id=p.equipo_visit_id)) hv,
            EXISTS (SELECT 1 FROM odds o WHERE o.partido_id=p.id
              AND o.mercado IN ('odds_local','odds_empate','odds_visitante')
              GROUP BY o.bookmaker HAVING count(DISTINCT o.mercado)=3) cuotas_1x2
          FROM partidos p WHERE p.estado IN ('NS','TBD','TDB')
            AND p.fecha >= now() - interval '1 day'
            AND p.fecha < now() + interval '7 days'
        )
        SELECT count(*) total_proximos,
          count(*) FILTER (WHERE hl<3 OR hv<3) sin_historial,
          count(*) FILTER (WHERE (hl<3 OR hv<3) AND cuotas_1x2) recuperables_por_cuotas
        FROM proximos;
        """
    else:
        sql = f"""
        SELECT e.id, e.nombre, e.sofascore_id,
               count(p.id) FILTER (WHERE p.estado = 'FT') AS finalizados,
               count(p.id) FILTER (WHERE p.estado = 'FT' AND p.equipo_local_id=e.id) AS de_local,
               count(p.id) FILTER (WHERE p.estado = 'FT' AND p.equipo_visit_id=e.id) AS de_visita,
               max(p.fecha) FILTER (WHERE p.estado = 'FT') AS ultimo_finalizado
        FROM equipos e
        LEFT JOIN partidos p
          ON p.equipo_local_id=e.id OR p.equipo_visit_id=e.id
        WHERE e.nombre ILIKE '%{termino}%'
        GROUP BY e.id, e.nombre, e.sofascore_id
        ORDER BY finalizados DESC, e.nombre;

        SELECT p.id AS partido_id, p.sofascore_id, p.fecha, l.nombre AS liga,
               el.nombre AS local, ev.nombre AS visitante,
               (SELECT count(*) FROM partidos h WHERE h.estado='FT'
                  AND h.fecha < p.fecha
                  AND (h.equipo_local_id=el.id OR h.equipo_visit_id=el.id)) AS historial_local,
               (SELECT count(*) FROM partidos h WHERE h.estado='FT'
                  AND h.fecha < p.fecha
                  AND (h.equipo_local_id=ev.id OR h.equipo_visit_id=ev.id)) AS historial_visitante,
               (SELECT count(*) FROM partidos h WHERE h.estado='FT'
                  AND h.fecha < p.fecha AND h.equipo_local_id=el.id) AS local_en_localia,
               (SELECT count(*) FROM partidos h WHERE h.estado='FT'
                  AND h.fecha < p.fecha AND h.equipo_visit_id=ev.id) AS visitante_en_localia
        FROM partidos p
        JOIN equipos el ON el.id=p.equipo_local_id
        JOIN equipos ev ON ev.id=p.equipo_visit_id
        JOIN ligas l ON l.id=p.liga_id
        WHERE p.estado IN ('NS','TBD','TDB')
          AND (el.nombre ILIKE '%{termino}%' OR ev.nombre ILIKE '%{termino}%')
        ORDER BY p.fecha DESC
        LIMIT 10;
        """
    host = os.environ["BETML_SSH_HOST"]
    user = os.environ["BETML_SSH_USER"]
    password = os.environ["BETML_SSH_PASS"]
    port = int(os.environ.get("BETML_SSH_PORT", "22"))

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=user, password=password, timeout=20)
    remote = (
        "docker exec betml-db sh -lc "
        + shlex.quote(
            'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -P pager=off -c '
            + shlex.quote(sql)
        )
    )
    _, stdout, stderr = client.exec_command(remote)
    output = stdout.read().decode("utf-8", errors="replace")
    error = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    client.close()
    if code:
        raise SystemExit(error or f"Consulta remota fallo ({code})")
    print(output)


if __name__ == "__main__":
    main()
