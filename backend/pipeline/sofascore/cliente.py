import time
import logging
import json
from typing import Optional
from playwright.sync_api import sync_playwright, Page, Browser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

BASE_URL = "https://api.sofascore.com/api/v1"

# IDs correctos de ligas — Liga MX corregido
LIGAS_SOFASCORE = {
    "Premier League":       17,
    "La Liga":              8,
    "Serie A":              23,
    "Bundesliga":           35,
    "Ligue 1":              34,
    "Champions League":     7,
    "Europa League":        679,
    "Conference League":    17015,
    "Copa Libertadores":    384,
    "Copa Sudamericana":    480,
    "Liga MX Apertura":     11621,  # ← separado en dos torneos
    "Liga MX Clausura":     11620,
    "MLS":                  242,
    "Brasileirao":          325,
    "Liga Argentina":       155,
    "LigaPro Ecuador":      240,
    "Eredivisie":           37,
    "Saudi Pro League":     955,
    # Nombres a la IZQUIERDA = como se llama la liga en NUESTRA BD
    # (backend/pipeline/config.py LIGAS), no como la llama Sofascore —
    # el cruce en job_alineaciones.py es por ese nombre. Ids sacados de
    # /sport/football/scheduled-tournaments/{fecha} (2026-08-12).
    "UEFA Super Cup":       465,   # Sofascore: "UEFA Super Cup"
    "Friendlies Clubs":     853,   # Sofascore: "Club Friendly Games"
}

# IDs de temporadas por liga — extraídos directamente de Sofascore
# Formato: {nombre_liga: {año_label: sofascore_season_id}}
TEMPORADAS_SOFASCORE = {
    "Premier League": {
        "23/24": 52186,
        "24/25": 61627,
        "25/26": 76986,
    },
    "La Liga": {
        "23/24": 52376,
        "24/25": 61643,
        "25/26": 77559,
    },
    "Serie A": {
        "23/24": 52760,
        "24/25": 63515,
        "25/26": 76457,
    },
    "Bundesliga": {
        "23/24": 52608,
        "24/25": 63516,
        "25/26": 77333,
    },
    "Ligue 1": {
        "23/24": 52571,
        "24/25": 61736,
        "25/26": 77356,
    },
    "Champions League": {
        "23/24": 52162,
        "24/25": 61644,
        "25/26": 76953,
    },
    "Europa League": {
        "23/24": 53654,
        "24/25": 61645,
        "25/26": 76984,
    },
    "Conference League": {
        "23/24": 52327,
        "24/25": 61648,
        "25/26": 76960,
    },
    "Copa Libertadores": {
        "2023": 47974,
        "2024": 57296,
        "2025": 70083,
    },
    "Copa Sudamericana": {
        "2023": 47968,
        "2024": 57297,
        "2025": 70070,
    },
    "Liga MX": {
        "2023": None,   # buscar ID correcto
        "2024": None,
    },
    "MLS": {
        "2023": 47955,
        "2024": 57317,
        "2025": 70158,
    },
    "Brasileirao": {
        "2023": 48982,
        "2024": 58766,
        "2025": 72034,
    },
    "Liga Argentina": {
        "2024": 57478,
        "2025_apertura": 70268,
        "2025_clausura": 77826,
    },
    "LigaPro Ecuador": {
        "2023": 48720,
        "2024": 58043,
        "2025": 71184,
    },
    "Eredivisie": {
        "23/24": 52554,
        "24/25": 61666,
        "25/26": 77012,
    },
    "Saudi Pro League": {
        "23/24": 53241,
        "24/25": 63998,
        "25/26": 80443,
    },
}

# Temporadas históricas que queremos descargar
# Son los IDs de Sofascore de las temporadas 23/24 y 24/25
TEMPORADAS_HISTORICAS = [
    # (nombre_liga, liga_id, season_id, label)
    ("Premier League",      17,    52186, "23/24"),
    ("Premier League",      17,    61627, "24/25"),
    ("Premier League",      17,    76986, "25/26"),
    ("La Liga",             8,     52376, "23/24"),
    ("La Liga",             8,     61643, "24/25"),
    ("La Liga",             8,     77559, "25/26"),
    ("Serie A",             23,    52760, "23/24"),
    ("Serie A",             23,    63515, "24/25"),
    ("Serie A",             23,    76457, "25/26"),
    ("Bundesliga",          35,    52608, "23/24"),
    ("Bundesliga",          35,    63516, "24/25"),
    ("Bundesliga",          35,    77333, "25/26"),
    ("Ligue 1",             34,    52571, "23/24"),
    ("Ligue 1",             34,    61736, "24/25"),
    ("Ligue 1",             34,    77356, "25/26"),
    ("Champions League",    7,     52162, "23/24"),
    ("Champions League",    7,     61644, "24/25"),
    ("Champions League",    7,     76953, "25/26"),
    ("Europa League",       679,   53654, "23/24"),
    ("Europa League",       679,   61645, "24/25"),
    ("Europa League",       679,   76984, "25/26"),
    ("Conference League",   17015, 52327, "23/24"),
    ("Conference League",   17015, 61648, "24/25"),
    ("Conference League",   17015, 76960, "25/26"),
    ("Copa Libertadores",   384,   47974, "2023"),
    ("Copa Libertadores",   384,   57296, "2024"),
    ("Copa Libertadores",   384,   70083, "2025"),
    ("Copa Sudamericana",   480,   47968, "2023"),
    ("Copa Sudamericana",   480,   57297, "2024"),
    ("Copa Sudamericana",   480,   70070, "2025"),
    ("Liga MX Apertura", 11621, 52052, "Apertura 2023"),
    ("Liga MX Apertura", 11621, 61419, "Apertura 2024"),
    ("Liga MX Apertura", 11621, 76500, "Apertura 2025"),
    ("Liga MX Apertura", 11621, 96191, "Apertura 2026"),
    ("Liga MX Clausura", 11620, 47656, "Clausura 2023"),
    ("Liga MX Clausura", 11620, 57315, "Clausura 2024"),
    ("Liga MX Clausura", 11620, 70096, "Clausura 2025"),
    ("Liga MX Clausura", 11620, 87699, "Clausura 2026"),
    ("MLS",                 242,   47955, "2023"),
    ("MLS",                 242,   57317, "2024"),
    ("MLS",                 242,   70158, "2025"),
    ("MLS",                 242,   86668, "2026"),
    ("Brasileirao",         325,   48982, "2023"),
    ("Brasileirao",         325,   58766, "2024"),
    ("Brasileirao",         325,   72034, "2025"),
    ("Brasileirao",         325,   87678, "2026"),
    ("Liga Argentina",      155,   47647, "2023"),
    ("Liga Argentina",      155,   57478, "2024"),
    ("Liga Argentina",      155,   70268, "Apertura 2025"),
    ("Liga Argentina",      155,   77826, "Clausura 2025"),
    ("Liga Argentina",      155,   87913, "2026"),
    ("LigaPro Ecuador",     240,   48720, "2023"),
    ("LigaPro Ecuador",     240,   58043, "2024"),
    ("LigaPro Ecuador",     240,   71184, "2025"),
    ("LigaPro Ecuador",     240,   89674, "2026"),
    ("Eredivisie",          37,    52554, "23/24"),
    ("Eredivisie",          37,    61666, "24/25"),
    ("Eredivisie",          37,    77012, "25/26"),
    ("Saudi Pro League",    955,   53241, "23/24"),
    ("Saudi Pro League",    955,   63998, "24/25"),
    ("Saudi Pro League",    955,   80443, "25/26"),
]

class SofascoreCliente:
    """
    Cliente de Sofascore usando Playwright.
    Lanza un browser Chromium real para evitar el bloqueo
    que Sofascore aplica a requests directos de Python.

    Patrón Singleton — una sola instancia del browser
    durante toda la ejecución del pipeline.
    """

    def __init__(self, headless: bool = True):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
        self.headless = headless

    def iniciar(self):
        """Arranca el browser y visita Sofascore para obtener cookies."""
        log.info("Iniciando browser Chromium...")
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
            ]
        )
        # Contexto con configuración de browser real
        context = self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="es-ES",
        )
        self._page = context.new_page()

        # Visita la página principal para obtener cookies válidas
        log.info("Visitando sofascore.com para obtener cookies...")
        self._page.goto(
            "https://www.sofascore.com/",
            wait_until="domcontentloaded",
            timeout=60000
        )
        time.sleep(2)
        log.info("Browser listo")

    def cerrar(self):
        """Cierra el browser limpiamente."""
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        log.info("Browser cerrado")

    def get(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """
        Hace una request a la API de Sofascore usando el browser.
        Navega directamente a la URL del endpoint JSON.
        """
        url = f"{BASE_URL}{endpoint}"
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query}"

        log.info(f"GET {url}")

        try:
            # Navega al endpoint JSON directamente
            response = self._page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000
            )

            if response.status == 429:
                log.warning("Rate limit — esperando 60 segundos")
                time.sleep(60)
                return self.get(endpoint, params)

            if response.status == 404:
                log.warning(f"404: {url}")
                return None

            if response.status != 200:
                log.error(f"Error {response.status}: {url}")
                return None

            # Extrae el JSON del contenido de la página
            content = self._page.content()

            # El JSON viene dentro de <pre> o <body>
            # Playwright lo renderiza como texto plano
            text = self._page.inner_text("body")
            data = json.loads(text)

            time.sleep(1.5)
            return data

        except json.JSONDecodeError as e:
            log.error(f"Error parseando JSON: {e}")
            return None
        except Exception as e:
            # Error de red/navegación (ej: internet caído) — NO es un 404.
            # Si esto devolviera None como un 404, el loop de paginación de
            # los jobs lo confunde con "se acabaron las páginas" y salta en
            # silencio el resto de la liga sin avisar (ya pasó: un corte de
            # internet a mitad de una corrida larga hizo que se saltearan
            # ligas enteras y el job igual reportó "OK" al final).
            # Se relanza para que el job se detenga y quede visible en el
            # log de error, en vez de terminar "limpio" con datos a medias.
            log.error(f"Error de red en request: {e}")
            raise

    def get_partidos_fecha(self, fecha: str) -> list:
        """Trae todos los partidos de fútbol de una fecha."""
        data = self.get(f"/sport/football/scheduled-events/{fecha}")
        if not data:
            return []
        eventos = data.get("events", [])
        log.info(f"Partidos encontrados en {fecha}: {len(eventos)}")
        return eventos

    def get_stats_partido(self, sofascore_id: int) -> Optional[list]:
        """Trae estadísticas completas de un partido."""
        data = self.get(f"/event/{sofascore_id}/statistics")
        if not data:
            return None
        return data.get("statistics", [])

    def get_lineups_partido(self, sofascore_id: int) -> Optional[dict]:
        """Trae alineaciones y stats de jugadores."""
        return self.get(f"/event/{sofascore_id}/lineups")

    def get_partidos_liga_temporada(
        self,
        liga_id: int,
        temporada_id: int,
        pagina: int = 0
    ) -> list:
        """Trae partidos históricos (ya jugados) de una liga y temporada
        — /events/last/, paginado hacia atrás desde el más reciente."""
        data = self.get(
            f"/unique-tournament/{liga_id}/season/{temporada_id}"
            f"/events/last/{pagina}"
        )
        if not data:
            return []
        return data.get("events", [])

    def get_partidos_liga_fecha(self, liga_id: int, fecha: str) -> list:
        """Partidos de una liga en una FECHA puntual — jugados, en vivo o
        por jugar. Es lo que hace falta para anclar sofascore_id de los
        partidos de hoy (ver job_alineaciones.py).

        Endpoint sacado de inspeccionar el tráfico real de sofascore.com
        (2026-08-12), no de adivinar rutas: es el mismo que su web usa
        para pintar la grilla del día. Las alternativas que se probaron
        antes fallan — /sport/football/scheduled-events/{fecha} da 404
        (en api. y en www.), y /events/next/ también 404. No requiere
        season_id, solo el id de torneo (LIGAS_SOFASCORE)."""
        data = self.get(f"/unique-tournament/{liga_id}/scheduled-events/{fecha}")
        if not data:
            return []
        return data.get("events", [])

    def get_temporadas_liga(self, liga_id: int) -> list:
        """Trae las temporadas disponibles de una liga."""
        data = self.get(f"/unique-tournament/{liga_id}/seasons")
        if not data:
            return []
        return data.get("seasons", [])

    def __enter__(self):
        """Permite usar el cliente con 'with' — abre el browser."""
        self.iniciar()
        return self

    def __exit__(self, *args):
        """Cierra el browser al salir del bloque 'with'."""
        self.cerrar()