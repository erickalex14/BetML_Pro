from backend.models.kelly import calcular_kelly, analizar_mercados_kelly

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