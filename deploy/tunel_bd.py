"""Túnel SSH a la base de producción, para desarrollar en local contra
los datos reales.

Se usa esto en vez de `ssh -L` porque el server autentica por
contraseña y el ssh de Windows la pide de forma interactiva — no se
puede dejar corriendo en segundo plano desde un script.

La base NO está expuesta a internet (escucha en 127.0.0.1 del server),
así que este túnel es la única forma de llegarle desde afuera, y eso es
a propósito.

    set BETML_SSH_HOST=... BETML_SSH_PORT=... BETML_SSH_USER=... BETML_SSH_PASS=...
    python deploy/tunel_bd.py

Dejalo corriendo en su propia terminal. Con el túnel arriba, el DB_URL
del .env (127.0.0.1:5434) pega contra la base de producción.

OJO: con esto conectado, cualquier script que corras en local escribe
en la base REAL. No hay red de contención.
"""
import os
import select
import socket
import sys
import threading

try:
    import paramiko
except ImportError:
    print("Falta paramiko: pip install paramiko", file=sys.stderr)
    sys.exit(1)

PUERTO_LOCAL = int(os.environ.get("BETML_TUNEL_PUERTO", "5434"))
DESTINO_HOST = "127.0.0.1"   # visto desde el server
DESTINO_PUERTO = 5434


class _Handler:
    def __init__(self, transporte):
        self.transporte = transporte

    def atender(self, cliente, direccion):
        try:
            canal = self.transporte.open_channel(
                "direct-tcpip", (DESTINO_HOST, DESTINO_PUERTO), cliente.getpeername())
        except Exception as e:
            print(f"No se pudo abrir el canal: {e}", file=sys.stderr)
            cliente.close()
            return
        if canal is None:
            cliente.close()
            return

        while True:
            r, _, _ = select.select([cliente, canal], [], [])
            if cliente in r:
                datos = cliente.recv(16384)
                if not datos:
                    break
                canal.sendall(datos)
            if canal in r:
                datos = canal.recv(16384)
                if not datos:
                    break
                cliente.sendall(datos)
        canal.close()
        cliente.close()


def main():
    host = os.environ.get("BETML_SSH_HOST")
    usuario = os.environ.get("BETML_SSH_USER")
    password = os.environ.get("BETML_SSH_PASS")
    puerto = int(os.environ.get("BETML_SSH_PORT", "22"))
    if not (host and usuario and password):
        print("Faltan BETML_SSH_HOST / BETML_SSH_USER / BETML_SSH_PASS", file=sys.stderr)
        sys.exit(1)

    cliente_ssh = paramiko.SSHClient()
    cliente_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cliente_ssh.connect(host, port=puerto, username=usuario, password=password, timeout=25)
    transporte = cliente_ssh.get_transport()
    handler = _Handler(transporte)

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(("127.0.0.1", PUERTO_LOCAL))
    servidor.listen(20)

    print(f"Tunel arriba: 127.0.0.1:{PUERTO_LOCAL} -> {host}:{DESTINO_PUERTO} (base de PRODUCCION)")
    print("Ctrl+C para cortarlo")

    try:
        while True:
            conexion, direccion = servidor.accept()
            threading.Thread(target=handler.atender, args=(conexion, direccion), daemon=True).start()
    except KeyboardInterrupt:
        print("\nTunel cerrado")
    finally:
        servidor.close()
        cliente_ssh.close()


if __name__ == "__main__":
    main()
