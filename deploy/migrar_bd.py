"""Copia la base local al Postgres de producción (una sola vez, para
arrancar con los datos que ya hay: ~16k partidos, stats de Sofascore,
cuotas, predicciones cerradas).

Tres pasos: pg_dump local -> subir por SFTP -> pg_restore adentro del
contenedor. Formato custom (-Fc) porque comprime y permite --clean, así
se puede correr de nuevo sin quedar con tablas duplicadas a medias.

Credenciales por variables de entorno, igual que deploy_betml.py:
    BETML_SSH_HOST / BETML_SSH_PORT / BETML_SSH_USER / BETML_SSH_PASS
La URL de la base local sale del .env del proyecto (DB_URL).

Requiere pg_dump instalado local (viene con Postgres; en Windows suele
estar en C:\\Program Files\\PostgreSQL\\<version>\\bin).
"""
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

try:
    import paramiko
except ImportError:
    print("Falta paramiko: pip install paramiko", file=sys.stderr)
    sys.exit(1)

RAIZ = Path(__file__).resolve().parent.parent
REMOTO = os.environ.get("BETML_REMOTE_DIR", "/home/novitecadmin/betml-stack/betml-pro")
DUMP_LOCAL = RAIZ / "betml_dump.pgdump"
DUMP_REMOTO = f"{REMOTO}/betml_dump.pgdump"


def _db_url_local() -> str:
    env = RAIZ / ".env"
    if env.exists():
        for linea in env.read_text(encoding="utf-8").splitlines():
            if linea.strip().startswith("DB_URL="):
                return linea.split("=", 1)[1].strip()
    url = os.environ.get("DB_URL")
    if not url:
        print("No encontré DB_URL ni en .env ni en el entorno", file=sys.stderr)
        sys.exit(1)
    return url


def dump_local():
    url = urlparse(_db_url_local().replace("postgresql+psycopg2://", "postgresql://"))
    entorno = dict(os.environ)
    if url.password:
        entorno["PGPASSWORD"] = url.password

    cmd = [
        os.environ.get("PG_DUMP", "pg_dump"),
        "-h", url.hostname or "localhost",
        "-p", str(url.port or 5432),
        "-U", url.username or "postgres",
        "-d", (url.path or "/betmlpro").lstrip("/"),
        "-Fc", "--no-owner", "--no-acl",
        "-f", str(DUMP_LOCAL),
    ]
    print("Generando dump local (puede tardar unos minutos)...")
    resultado = subprocess.run(cmd, env=entorno, capture_output=True, text=True)
    if resultado.returncode != 0:
        print(resultado.stderr, file=sys.stderr)
        print("Falló pg_dump. Si no está en el PATH, pasá la ruta completa "
              "en la variable PG_DUMP.", file=sys.stderr)
        sys.exit(1)
    mb = DUMP_LOCAL.stat().st_size / 1024 / 1024
    print(f"Dump listo: {DUMP_LOCAL.name} ({mb:.1f} MB)")


def subir_y_restaurar():
    host = os.environ.get("BETML_SSH_HOST")
    usuario = os.environ.get("BETML_SSH_USER")
    password = os.environ.get("BETML_SSH_PASS")
    puerto = int(os.environ.get("BETML_SSH_PORT", "22"))
    if not (host and usuario and password):
        print("Faltan BETML_SSH_HOST / BETML_SSH_USER / BETML_SSH_PASS", file=sys.stderr)
        sys.exit(1)

    cliente = paramiko.SSHClient()
    cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cliente.connect(host, port=puerto, username=usuario, password=password, timeout=20)

    print("Subiendo dump...")
    sftp = cliente.open_sftp()
    sftp.put(str(DUMP_LOCAL), DUMP_REMOTO)
    sftp.close()
    print("Dump subido")

    usuario_db = os.environ.get("POSTGRES_USER", "betml")
    nombre_db = os.environ.get("POSTGRES_DB", "betml")

    comandos = [
        f"docker cp {DUMP_REMOTO} betml-db:/tmp/betml_dump.pgdump",
        # --clean: si ya había datos de una corrida anterior, los pisa en
        # vez de chocar con claves duplicadas
        f"docker exec betml-db pg_restore -U {usuario_db} -d {nombre_db} "
        f"--clean --if-exists --no-owner /tmp/betml_dump.pgdump || true",
        f"docker exec betml-db psql -U {usuario_db} -d {nombre_db} -c "
        f"\"select 'partidos: ' || count(*) from partidos\"",
    ]
    for cmd in comandos:
        print(f"\n$ {cmd}")
        _, stdout, stderr = cliente.exec_command(cmd)
        print(stdout.read().decode("utf-8", errors="ignore"), end="")
        err = stderr.read().decode("utf-8", errors="ignore").strip()
        if err:
            # pg_restore escribe avisos por stderr aunque haya ido bien
            print(f"[stderr] {err}")

    cliente.close()
    print("\nMigración terminada")


if __name__ == "__main__":
    dump_local()
    subir_y_restaurar()
