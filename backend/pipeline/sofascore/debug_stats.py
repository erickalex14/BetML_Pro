from backend.pipeline.sofascore.cliente import SofascoreCliente

def main():
    with SofascoreCliente(headless=True) as cliente:
        # Trae stats de Brentford vs Fulham (primer partido guardado)
        stats = cliente.get_stats_partido(11352485)

        if not stats:
            print("Sin stats")
            return

        print("Nombres EXACTOS de estadísticas en Sofascore:")
        print("=" * 60)

        for grupo_periodo in stats:
            if grupo_periodo.get("period") == "ALL":
                for grupo in grupo_periodo.get("groups", []):
                    print(f"\n[{grupo.get('groupName')}]")
                    for item in grupo.get("statisticsItems", []):
                        print(
                            f"  '{item['name']}'"
                            f" → L:{item.get('home')}"
                            f" V:{item.get('away')}"
                        )

if __name__ == "__main__":
    main()