from backend.pipeline.config import LIGAS
from backend.pipeline import api_client

def main():
    print("\n" + "="*50)
    print("  TEST DE CONEXIÓN — BetML Pro")
    print("="*50 + "\n")

    # TEST 1: Fixtures de hoy en Premier League
    print("TEST 1: Partidos de hoy en Premier League")
    print("-" * 40)

    partidos = api_client.get_fixtures_hoy(
        liga_id=LIGAS["Premier League"],
        temporada=2024
    )

    if partidos:
        print(f"Encontrados: {len(partidos)} partidos\n")
        for p in partidos[:3]:      # muestra máximo 3
            local     = p["teams"]["home"]["name"]
            visitante = p["teams"]["away"]["name"]
            hora      = p["fixture"]["date"][11:16]  # "HH:MM"
            print(f"  {hora}  {local}  vs  {visitante}")
    else:
        print("Sin partidos hoy en Premier (normal si no hay fecha)")

    # TEST 2: Tabla de posiciones La Liga
    print("\nTEST 2: Top 3 de La Liga")
    print("-" * 40)

    standings = api_client.get_standings(
        liga_id=LIGAS["La Liga"],
        temporada=2024
    )

    if standings:
        # La estructura viene anidada: response[0][0] es la liga
        equipos = standings[0]["league"]["standings"][0]
        for equipo in equipos[:3]:
            pos    = equipo["rank"]
            nombre = equipo["team"]["name"]
            pts    = equipo["points"]
            print(f"  {pos}. {nombre} — {pts} pts")
    else:
        print("Error trayendo standings")

    print("\n" + "="*50)
    print("  Si ves datos arriba — todo funciona!")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()