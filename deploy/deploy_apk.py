"""Publica un APK versionado de BetML sin borrar versiones anteriores.

Credenciales y destinos se leen de BETML_SSH_* / BETML_APK_REMOTE_DIR.
La subida es atómica: primero .uploading, después rename y checksum remoto.
"""
import argparse
import hashlib
import os
import posixpath
import sys
from pathlib import Path

import paramiko


def ejecutar(cliente: paramiko.SSHClient, comando: str) -> str:
    _, stdout, stderr = cliente.exec_command(comando)
    salida = stdout.read().decode("utf-8", errors="replace")
    error = stderr.read().decode("utf-8", errors="replace")
    codigo = stdout.channel.recv_exit_status()
    if codigo:
        raise RuntimeError(f"Comando remoto falló ({codigo}): {error or salida}")
    return salida.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("apk", type=Path)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()

    host = os.environ.get("BETML_SSH_HOST")
    user = os.environ.get("BETML_SSH_USER")
    password = os.environ.get("BETML_SSH_PASS")
    port = int(os.environ.get("BETML_SSH_PORT", "22"))
    remote_dir = os.environ.get(
        "BETML_APK_REMOTE_DIR", "/home/novitecadmin/betml-stack/apk"
    ).rstrip("/")
    if not all((host, user, password)):
        raise SystemExit("Faltan BETML_SSH_HOST, BETML_SSH_USER o BETML_SSH_PASS")
    if not args.apk.is_file() or args.apk.suffix.lower() != ".apk":
        raise SystemExit(f"APK inválido: {args.apk}")
    if "/" in args.name or "\\" in args.name or not args.name.endswith(".apk"):
        raise SystemExit("--name debe ser un nombre .apk sin directorios")

    local_hash = hashlib.sha256(args.apk.read_bytes()).hexdigest()
    destino = posixpath.join(remote_dir, args.name)
    temporal = f"{destino}.uploading"

    cliente = paramiko.SSHClient()
    cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cliente.connect(host, port=port, username=user, password=password, timeout=20)
    try:
        ejecutar(cliente, f"test -d '{remote_dir}' && test -w '{remote_dir}'")
    except RuntimeError:
        directorios = ejecutar(
            cliente,
            "find /www/wwwroot /home/novitecadmin -maxdepth 5 "
            "-type d -iname '*betml*' 2>/dev/null || true",
        )
        apks = ejecutar(
            cliente,
            "find /home/novitecadmin /www/wwwroot -maxdepth 7 "
            "-type f -name '*.apk' 2>/dev/null | head -30 || true",
        )
        nginx = ejecutar(
            cliente,
            "grep -R -n -E 'betml-apk|location /betml' "
            "/www/server/panel/vhost/nginx /home/novitecadmin 2>/dev/null "
            "| head -30 || true",
        )
        detalle = f"directorios=[{directorios}] apks=[{apks}] nginx=[{nginx}]"
        raise RuntimeError(
            f"Destino inexistente o no escribible: {remote_dir}. Candidatos: {detalle}"
        )

    sftp = cliente.open_sftp()
    try:
        sftp.put(str(args.apk), temporal)
        sftp.rename(temporal, destino)
        sftp.chmod(destino, 0o644)
    finally:
        sftp.close()

    remote_hash = ejecutar(cliente, f"sha256sum '{destino}' | cut -d' ' -f1")
    if remote_hash != local_hash:
        raise RuntimeError("Checksum remoto no coincide; el enlace latest no fue actualizado")
    ejecutar(
        cliente,
        f"cd '{remote_dir}' && ln -sfn '{args.name}' betml-latest.apk",
    )
    cliente.close()
    print(f"APK publicado: {args.name}")
    print(f"SHA256: {local_hash}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
