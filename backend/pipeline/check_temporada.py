from backend.pipeline import api_client

# Revisa temporada actual de las ligas principales
ligas_check = {
    "Premier League":    39,
    "La Liga":           140,
    "Copa Libertadores": 13,
    "LigaPro Ecuador":   314,
}

for nombre, liga_id in ligas_check.items():
    data = api_client.get("/leagues", params={
        "current": "true",
        "id": liga_id
    })

    for r in data.get("response", []):
        for season in r.get("seasons", []):
            if season.get("current"):
                print(f"{nombre}")
                print(f"  Temporada : {season['year']}")
                print(f"  Inicio    : {season['start']}")
                print(f"  Fin       : {season['end']}")
                print()