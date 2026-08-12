import '../../domain/entities/parlay.dart';

class ParlayResultadoModel extends ParlayResultado {
  const ParlayResultadoModel({
    required super.probCombinada,
    required super.cuotaCombinada,
    required super.stakePct,
    required super.stakeUnits,
    required super.bankroll,
    required super.esValueBet,
    required super.ev,
    super.parlayId,
  });

  factory ParlayResultadoModel.fromJson(Map<String, dynamic> json) {
    final kelly = json['kelly'] as Map<String, dynamic>? ?? {};
    return ParlayResultadoModel(
      probCombinada: (json['prob_combinada'] ?? 0.0).toDouble(),
      cuotaCombinada: (json['cuota_combinada'] ?? 0.0).toDouble(),
      stakePct: (json['stake_pct'] ?? 0.0).toDouble(),
      stakeUnits: (json['stake_units'] ?? 0.0).toDouble(),
      bankroll: (json['bankroll'] ?? 0.0).toDouble(),
      esValueBet: kelly['es_value_bet'] ?? false,
      ev: (kelly['ev'] ?? 0.0).toDouble(),
      parlayId: json['parlay_id'] as int?,
    );
  }
}
