from backend.models.montecarlo import simular_partido

# Simula un partido con xG reales — con mercados de corners y tarjetas
resultado = simular_partido(
    xg_local=1.8,
    xg_visitante=0.9,
    n_simulaciones=10000,
    corners_local=5.8,
    corners_visit=4.1,
    amarillas_local=2.0,
    amarillas_visit=2.3,
)

print("=" * 55)
print("  Monte Carlo — 10,000 simulaciones")
print("=" * 55)
print(f"\nxG Local: {resultado['xg_local']} | xG Visit: {resultado['xg_visitante']}")
print(f"\nProbabilidades 1X2:")
print(f"  Local:     {resultado['prob_local']*100:.1f}%")
print(f"  Empate:    {resultado['prob_empate']*100:.1f}%")
print(f"  Visitante: {resultado['prob_visitante']*100:.1f}%")

print(f"\nTop 5 marcadores más probables:")
for m in resultado["top_marcadores"][:5]:
    barra = "█" * int(m["porcentaje"])
    print(f"  {m['marcador']:<6} {m['porcentaje']:>5.1f}% {barra}")

print(f"\nOver/Under:")
ou = resultado["over_under"]
print(f"  Over 0.5:  {ou['over_0_5']*100:.1f}%")
print(f"  Over 1.5:  {ou['over_1_5']*100:.1f}%")
print(f"  Over 2.5:  {ou['over_2_5']*100:.1f}%")
print(f"  Over 3.5:  {ou['over_3_5']*100:.1f}%")

print(f"\nBTTS:")
print(f"  Sí: {resultado['btts_si']*100:.1f}%")
print(f"  No: {resultado['btts_no']*100:.1f}%")

print(f"\nPromedio goles totales: {resultado['prom_goles_total']}")
print(f"Incertidumbre: {resultado['incertidumbre']*100:.1f}%")
print(f"\nPercentiles goles totales:")
for p, v in resultado["percentiles_goles_totales"].items():
    print(f"  {p}: {v} goles")

print(f"\nCorners (over/under):")
for k, v in resultado["corners"]["over_under"].items():
    print(f"  {k}: {v*100:.1f}%")

print(f"\nTarjetas (over/under):")
for k, v in resultado["tarjetas"]["over_under"].items():
    print(f"  {k}: {v*100:.1f}%")