"""Sube BetML Pro al servidor y reconstruye los contenedores.

Mismo patrón que el script de deploy de novitec-sgn (SFTP + docker
compose por SSH), con dos diferencias a propósito:

1. Las credenciales NO van escritas acá — salen de variables de entorno.
   Un script con la contraseña adentro termina commiteado tarde o
   temprano; si esto se sube al repo, no se filtra nada.
       set BETML_SSH_HOST=...      (o export en Linux)
       set BETML_SSH_PORT=...
       set BETML_SSH_USER=...
       set BETML_SSH_PASS=...

2. Sube el proyecto entero filtrando lo que no va (git, venv, datos,
   .env), en vez de solo el diff contra origin/main — este repo todavía
   no tiene remoto, así que "diff contra origin" no aplica.

El .env de producción NO se sube: se crea a mano en el server una sola
vez (tiene la API key, el secreto JWT y la URL de la base).
"""
import os
import sys
import stat
from pathlib import Path

try:
    import paramiko
except ImportError:
    print("Falta paramiko: pip install paramiko", file=sys.stderr)
    sys.exit(1)

RAIZ = Path(__file__).resolve().parent.parent
REMOTO = os.environ.get("BETML_REMOTE_DIR", "/home/novitecadmin/betml-stack/betml-pro")

# Lo que NO se sube: pesado, secreto o regenerable en el server
EXCLUIR_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules",
    "graphify-out", "build", ".dart_tool", "logs", "scratch",
}
EXCLUIR_ARCHIVOS = {".env", ".env.local"}
EXCLUIR_SUFIJOS = {".pyc", ".log", ".pkl.bak", ".apk"}

# frontend/ no va al server: es la app del celular, se compila aparte y
# se reparte como APK. Subirla sería mandar cientos de MB al pedo.
EXCLUIR_TOP = {"frontend"}


def archivos_a_subir():
    for ruta in RAIZ.rglob("*"):
        if ruta.is_dir():
            continue
        rel = ruta.relative_to(RAIZ)
        partes = rel.parts
        if partes[0] in EXCLUIR_TOP:
            continue
        if any(p in EXCLUIR_DIRS for p in partes):
            continue
        if ruta.name in EXCLUIR_ARCHIVOS or ruta.suffix in EXCLUIR_SUFIJOS:
            continue
        # los modelos entrenados SÍ van (la API no predice sin ellos),
        # pero el dataset cacheado no — se regenera solo y pesa mucho
        if rel.as_posix().startswith("data/") and not rel.as_posix().startswith("data/models/"):
            continue
        yield rel


def mkdir_p(sftp, directorio: str):
    actual = ""
    for parte in directorio.split("/"):
        if not parte:
            continue
        actual += "/" + parte
        try:
            sftp.stat(actual)
        except IOError:
            sftp.mkdir(actual)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    host = os.environ.get("BETML_SSH_HOST")
    usuario = os.environ.get("BETML_SSH_USER")
    password = os.environ.get("BETML_SSH_PASS")
    puerto = int(os.environ.get("BETML_SSH_PORT", "22"))

    if not (host and usuario and password):
        print("Faltan BETML_SSH_HOST / BETML_SSH_USER / BETML_SSH_PASS "
              "en las variables de entorno.", file=sys.stderr)
        sys.exit(1)

    archivos = list(archivos_a_subir())
    print(f"{len(archivos)} archivos a subir a {host}:{puerto}{REMOTO}")

    cliente = paramiko.SSHClient()
    cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cliente.connect(host, port=puerto, username=usuario, password=password, timeout=20)
    print("SSH conectado")

    sftp = cliente.open_sftp()
    for rel in archivos:
        destino = f"{REMOTO}/{rel.as_posix()}"
        mkdir_p(sftp, os.path.dirname(destino))
        sftp.put(str(RAIZ / rel), destino)
    sftp.close()
    print("Archivos subidos")

    comandos = [
        f"test -f {REMOTO}/.env || echo 'FALTA {REMOTO}/.env — crealo antes de levantar'",
        f"cd {REMOTO} && docker compose -f docker-compose.prod.yml up -d --build",
        "docker ps --filter name=betml --format '{{.Names}}: {{.Status}}'",
    ]
    for cmd in comandos:
        print(f"\n$ {cmd}")
        _, stdout, stderr = cliente.exec_command(cmd)
        print(stdout.read().decode("utf-8", errors="ignore"), end="")
        err = stderr.read().decode("utf-8", errors="ignore").strip()
        if err:
            print(f"[stderr] {err}")

    cliente.close()
    print("\nDeploy terminado")


if __name__ == "__main__":
    main()
