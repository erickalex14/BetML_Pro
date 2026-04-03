import requests          # librería HTTP
import os               # para leer variables del sistema
from dotenv import load_dotenv  # carga el .env

# Carga las variables del archivo .env
load_dotenv()

# Lee la API key del .env
API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = os.getenv("API_FOOTBALL_BASE_URL")

# Headers requeridos por API-Football
headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "v3.football.api-sports.io"
}

# Hace la petición: trae las ligas disponibles
response = requests.get(
    f"{BASE_URL}/leagues",
    headers=headers,
    params={"name": "Premier League"}  # filtra por nombre
)

# response.json() convierte la respuesta a dict de Python
data = response.json()

# Imprime cuántas ligas encontró
print(f"Status: {response.status_code}")
print(f"Resultados: {data['results']}")
print(f"Primera liga: {data['response'][0]['league']['name']}")