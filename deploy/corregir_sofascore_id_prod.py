"""Retira un sofascore_id incorrecto solo si partido e ID aún coinciden."""
import os
import shlex
import sys

import paramiko


partido_id, sofascore_id = map(int, sys.argv[1:3])
sql = (
    f"UPDATE partidos SET sofascore_id=NULL WHERE id={partido_id} "
    f"AND sofascore_id={sofascore_id} RETURNING id, sofascore_id;"
)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(os.environ["BETML_SSH_HOST"],
               port=int(os.environ.get("BETML_SSH_PORT", "22")),
               username=os.environ["BETML_SSH_USER"],
               password=os.environ["BETML_SSH_PASS"], timeout=20)
cmd = "docker exec betml-db sh -lc " + shlex.quote(
    'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c ' + shlex.quote(sql))
_, stdout, stderr = client.exec_command(cmd)
salida, error = stdout.read().decode(), stderr.read().decode()
codigo = stdout.channel.recv_exit_status()
client.close()
print(salida)
raise SystemExit(codigo or bool(error))
