"""Descarga en solo lectura el dataset cacheado del scheduler de producción."""
import hashlib
import os
import shlex
from pathlib import Path

import paramiko


RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "data" / "dataset_features.prod.pkl"
REMOTO_APP = os.environ.get("BETML_REMOTE_DIR", "/home/novitecadmin/betml-stack/betml-pro")
REMOTO_TMP = f"{REMOTO_APP}/dataset_features.prod.tmp.pkl"
CONTENEDOR = "betml-scheduler"
ORIGEN = "/app/data/dataset_features.pkl"


def _ejecutar(cliente, comando: str) -> str:
    _, stdout, stderr = cliente.exec_command(comando)
    salida = stdout.read().decode("utf-8", errors="replace")
    error = stderr.read().decode("utf-8", errors="replace")
    codigo = stdout.channel.recv_exit_status()
    if codigo:
        raise RuntimeError(error or salida or f"Comando remoto falló: {codigo}")
    return salida.strip()


def descargar() -> Path:
    host = os.environ["BETML_SSH_HOST"]
    usuario = os.environ["BETML_SSH_USER"]
    password = os.environ["BETML_SSH_PASS"]
    puerto = int(os.environ.get("BETML_SSH_PORT", "22"))

    cliente = paramiko.SSHClient()
    cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cliente.connect(host, port=puerto, username=usuario, password=password, timeout=20)
    origen = shlex.quote(f"{CONTENEDOR}:{ORIGEN}")
    temporal = shlex.quote(REMOTO_TMP)
    try:
        hash_remoto = _ejecutar(
            cliente, f"docker exec {CONTENEDOR} sha256sum {shlex.quote(ORIGEN)}"
        ).split()[0]
        _ejecutar(cliente, f"docker cp {origen} {temporal}")
        sftp = cliente.open_sftp()
        try:
            DESTINO.parent.mkdir(parents=True, exist_ok=True)
            sftp.get(REMOTO_TMP, str(DESTINO))
            sftp.remove(REMOTO_TMP)
        finally:
            sftp.close()
    finally:
        cliente.close()

    hash_local = hashlib.sha256(DESTINO.read_bytes()).hexdigest()
    if hash_local != hash_remoto:
        raise RuntimeError("El hash del dataset descargado no coincide con producción")
    print(f"Dataset verificado: {DESTINO} ({DESTINO.stat().st_size} bytes, sha256={hash_local[:12]}…)")
    return DESTINO


if __name__ == "__main__":
    descargar()
