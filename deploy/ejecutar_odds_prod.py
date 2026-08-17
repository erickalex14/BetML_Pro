"""Ejecuta una vez la cascada de cuotas dentro del scheduler de producción."""
import os
import sys

import paramiko


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        os.environ["BETML_SSH_HOST"],
        port=int(os.environ.get("BETML_SSH_PORT", "22")),
        username=os.environ["BETML_SSH_USER"],
        password=os.environ["BETML_SSH_PASS"],
        timeout=20,
    )
    comando = (
        "docker exec betml-scheduler python -m "
        "backend.pipeline.odds.orquestador"
    )
    _, stdout, _ = client.exec_command(f"{comando} 2>&1")
    for linea in iter(stdout.readline, ""):
        print(linea, end="")
    codigo = stdout.channel.recv_exit_status()
    client.close()
    raise SystemExit(codigo)


if __name__ == "__main__":
    main()
