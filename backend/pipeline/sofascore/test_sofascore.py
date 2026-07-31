from backend.pipeline.sofascore.cliente import SofascoreCliente



def main():
    print("\n" + "=" * 55)
    print("  TEST — Partidos históricos Sofascore")
    print("=" * 55 + "\n")

    with SofascoreCliente(headless=True) as cliente:

        # Prueba con Premier League 23/24 — season_id 52186
        print("Premier League 23/24 — últimos partidos:")
        print("-" * 40)

        partidos = cliente.get_partidos_liga_temporada(
            liga_id=17,
            temporada_id=52186,
            pagina=0
        )

        print(f"Partidos encontrados: {len(partidos)}")
        for p in partidos[:5]:
            home   = p.get("homeTeam", {}).get("name", "?")
            away   = p.get("awayTeam", {}).get("name", "?")
            status = p.get("status", {}).get("type", "?")
            gl     = p.get("homeScore", {}).get("current", "?")
            ga     = p.get("awayScore", {}).get("current", "?")
            sid    = p.get("id")
            print(f"  ID:{sid} {home} {gl}-{ga} {away} [{status}]")

        # Prueba stats del primer partido terminado
        if partidos:
            partido_ft = next(
                (p for p in partidos
                 if p.get("status", {}).get("type") == "finished"),
                None
            )
            if partido_ft:
                sid  = partido_ft.get("id")
                home = partido_ft.get("homeTeam", {}).get("name")
                away = partido_ft.get("awayTeam", {}).get("name")

                print(f"\nStats de: {home} vs {away} (ID: {sid})")
                print("-" * 40)

                stats = cliente.get_stats_partido(sid)
                if stats:
                    for grupo_periodo in stats:
                        if grupo_periodo.get("period") == "ALL":
                            for grupo in grupo_periodo.get("groups", []):
                                print(f"\n  {grupo.get('groupName')}:")
                                for item in grupo.get("statisticsItems", []):
                                    print(
                                        f"    {item['name']:<30} "
                                        f"L:{item.get('home'):<6} "
                                        f"V:{item.get('away')}"
                                    )
                else:
                    print("  Sin stats")

    print("\n" + "=" * 55)


if __name__ == "__main__":
    main()