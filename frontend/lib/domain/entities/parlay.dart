class ParlaySeleccionInput {
  final int partidoId;
  final String mercado;
  final double? cuota;
  const ParlaySeleccionInput({
    required this.partidoId,
    required this.mercado,
    this.cuota,
  });

  Map<String, dynamic> toJson() => {
        'partido_id': partidoId,
        'mercado': mercado,
        if (cuota != null) 'cuota': cuota,
      };
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
