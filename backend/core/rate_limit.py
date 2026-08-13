from slowapi import Limiter
from slowapi.util import get_ipaddr

from backend.core.auth import verificar_token


def usuario_o_ip(request):
    autorizacion = request.headers.get("Authorization", "")
    if autorizacion.startswith("Bearer "):
        payload = verificar_token(autorizacion[7:])
        if payload:
            return f"usuario:{payload['sub']}"
    return get_ipaddr(request)


limiter = Limiter(key_func=get_ipaddr, default_limits=["300/minute"])
