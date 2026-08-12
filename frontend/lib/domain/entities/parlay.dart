class ParlaySeleccionInput {
  final int partidoId;
  final String mercado; // "local" | "empate" | "visitante"
  const ParlaySeleccionInput({required this.partidoId, required this.mercado});

  Map<String, dynamic> toJson() => {'partido_id': partidoId, 'mercado': mercado};
}

class ParlayResultado {
  final double probCombinada;
  final double cuotaCombinada;
  final double stakePct;
  final double stakeUnits;
  final double bankroll;
  final bool esValueBet;
  final double ev;
  final int? parlayId;

  const ParlayResultado({
    required this.probCombinada,
    required this.cuotaCombinada,
    required this.stakePct,
    required this.stakeUnits,
    required this.bankroll,
    required this.esValueBet,
    required this.ev,
    this.parlayId,
  });
}
