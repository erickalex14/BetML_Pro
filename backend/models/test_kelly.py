from backend.models.kelly import calcular_kelly, analizar_mercados_kelly
from backend.models.montecarlo import simular_partido

# Test 1 — Kelly simple
print("Kelly para Local (55% prob, cuota 2.10):")
k = calcular_kelly(0.55, 2.10)
for key, val in k.items():
    print(f"  {key}: {val}")

print()

# Test 2 — Analisis completo de partido
pred = {
    "prob_local":     0.55,
    "prob_empate":    0.25,
    "prob_visitante": 0.20,
}
odds = {
    "odds_local":     2.10,
    "odds_empate":    3.40,
    "odds_visitante": 4.50,
}

resultado = analizar_mercados_kelly(
    prediccion=pred,
    odds=odds,
    bankroll=1000
)

print(f"Value bets encontradas: {resultado['n_value_bets']}")

for vb in resultado["value_bets"]:
    print(
        f"  {vb['mercado']}: "
        f"stake={vb['stake_pct']}% "
        f"({vb['stake_units']} unidades) | "
        f"EV={vb['ev']} | "
        f"Edge={vb['edge']}"
    )

print()

# Test 3 — Sin value bet
print("Sin value bet (30% prob, cuota 2.10):")
k2 = calcular_kelly(0.30, 2.10)
print(f"  es_value_bet: {k2['es_value_bet']}")
print(f"  mensaje: {k2['mensaje']}")
print(f"  EV: {k2['ev']}")

print()

# Test 4 — Mercados extra vía Monte Carlo (Over/Under, BTTS, corners, tarjetas)
mc = simular_partido(1.8, 0.9, n_simulaciones=20000,
                      corners_local=5.8, corners_visit=4.1,
                      amarillas_local=2.0, amarillas_visit=2.3)

odds_extra = {
    **odds,
    "odds_goles_over_2_5": 1.85, "odds_goles_under_2_5": 2.00,
    "odds_btts_si": 1.75, "odds_btts_no": 2.05,
    "odds_corners_over_9_5": 1.90,
    "odds_tarjetas_over_2_5": 1.80,
}
resultado_extra = analizar_mercados_kelly(pred, odds_extra, bankroll=1000, montecarlo=mc)

print(f"Mercados analizados con Monte Carlo: {len(resultado_extra['todos_mercados'])}")
assert len(resultado_extra["todos_mercados"]) > 3, "deberia sumar mercados mas alla de 1X2"
for m in resultado_extra["todos_mercados"]:
    print(f"  {m['mercado']:<20} prob={m['probabilidad']:.3f} ev={m['ev']:+.3f} value={m['es_value_bet']}")

# Test 5 — factor_confianza reduce el stake sin negar el value bet
k_normal = calcular_kelly(0.55, 2.10, fraccion=0.25, factor_confianza=1.0)
k_reducido = calcular_kelly(0.55, 2.10, fraccion=0.25, factor_confianza=0.5)
assert k_reducido["stake_kelly"] < k_normal["stake_kelly"]
assert k_reducido["es_value_bet"] == k_normal["es_value_bet"] == True
print(f"\nfactor_confianza=1.0 -> stake {k_normal['stake_kelly']*100:.2f}%")
print(f"factor_confianza=0.5 -> stake {k_reducido['stake_kelly']*100:.2f}% (mismo edge, menos data validada)")