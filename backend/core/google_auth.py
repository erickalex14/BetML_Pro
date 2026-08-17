from google.auth.transport.requests import Request
from google.oauth2 import id_token

from backend.core.config import get_settings


def verificar_id_token_google(token: str) -> dict:
    return id_token.verify_oauth2_token(token, Request(), get_settings().google_client_id)
