import '../../domain/entities/recomendadas.dart';

class ApuestaIndividualModel extends ApuestaIndividual {
  const ApuestaIndividualModel({
    required super.partidoId,
    required super.local,
    required super.visitante,
    required super.liga,
    required super.mercado,
    required super.probabilidad,
    required super.cuota,
    required super.ev,
    required super.edge,
    required super.stakePct,
  });

  factory ApuestaIndividualModel.fromJson(Map<String, dynamic> json) {
    return ApuestaIndividualModel(
      partidoId: json['partido_id'] ?? 0,
      local: json['local'] ?? '',
      visitante: json['visitante'] ?? '',
      liga: json['liga'] ?? '',
      mercado: json['mercado'] ?? '',
      probabilidad: (json['probabilidad'] ?? 0.0).toDouble(),
      cuota: (json['cuota'] ?? 0.0).toDouble(),
      ev: (json['ev'] ?? 0.0).toDouble(),
      edge: (json['edge'] ?? 0.0).toDouble(),
      stakePct: (json['stake_pct'] ?? 0.0).toDouble(),
    );
  }
}

class MercadoCombinadaModel extends MercadoCombinada {
  const MercadoCombinadaModel({
    required super.nombre,
    required super.cuota,
    required super.probabilidad,
    required super.stakePct,
  });

  factory MercadoCombinadaModel.fromJson(Map<String, dynamic> json) {
    return MercadoCombinadaModel(
      nombre: json['mercado'] ?? '',
      cuota: (json['cuota'] ?? 0.0).toDouble(),
      probabilidad: (json['probabilidad'] ?? 0.0).toDouble(),
      stakePct: (json['stake_pct'] ?? 0.0).toDouble(),
    );
  }
}

class CombinadaMismoPartidoModel extends CombinadaMismoPartido {
  const CombinadaMismoPartidoModel({
    required super.partidoId,
    required super.local,
    required super.visitante,
    required super.liga,
    required super.mercados,
    required super.stakeTotalPct,
    required super.evPortafolio,
  });

  factory CombinadaMismoPartidoModel.fromJson(Map<String, dynamic> json) {
    final portafolio = json['portafolio'] as Map<String, dynamic>? ?? {};
    return CombinadaMismoPartidoModel(
      partidoId: json['partido_id'] ?? 0,
      local: json['local'] ?? '',
      visitante: json['visitante'] ?? '',
      liga: json['liga'] ?? '',
      mercados: (portafolio['mercados'] as List? ?? [])
          .map((m) => MercadoCombinadaModel.fromJson(m))
          .where((m) => m.stakePct > 0)
          .toList(),
      stakeTotalPct: (portafolio['stake_total_pct'] ?? 0.0).toDouble(),
      evPortafolio: (portafolio['ev_portafolio'] ?? 0.0).toDouble(),
    );
  }
}

class PataParlayModel extends PataParlay {
  const PataParlayModel({
    required super.partidoId,
    required super.local,
    required super.visitante,
    required super.mercado,
  });

  factory PataParlayModel.fromJson(Map<String, dynamic> json) {
    return PataParlayModel(
      partidoId: json['partido_id'] ?? 0,
      local: json['local'] ?? '',
      visitante: json['visitante'] ?? '',
      mercado: json['mercado'] ?? '',
    );
  }
}

class ParlaySugeridoModel extends ParlaySugerido {
  const ParlaySugeridoModel({
    required super.nPatas,
    required super.selecciones,
    required super.probCombinada,
    required super.cuotaCombinada,
    required super.stakePct,
    required super.ev,
  });

  factory ParlaySugeridoModel.fromJson(Map<String, dynamic> json) {
    final kelly = json['kelly'] as Map<String, dynamic>? ?? {};
    return ParlaySugeridoModel(
      nPatas: json['n_patas'] ?? 0,
      selecciones: (json['selecciones'] as List? ?? [])
          .map((s) => PataParlayModel.fromJson(s))
          .toList(),
      probCombinada: (json['prob_combinada'] ?? 0.0).toDouble(),
      cuotaCombinada: (json['cuota_combinada'] ?? 0.0).toDouble(),
      stakePct: (json['stake_pct'] ?? 0.0).toDouble(),
      ev: (kelly['ev'] ?? 0.0).toDouble(),
    );
  }
}

class RecomendadasModel extends Recomendadas {
  const RecomendadasModel({
    required super.fecha,
    required super.individualesFijas,
    required super.individualesSonadoras,
    required super.combinadasFijas,
    required super.combinadasSonadoras,
    required super.parlaysFijas,
    required super.parlaysSonadoras,
  });

  factory RecomendadasModel.fromJson(Map<String, dynamic> json) {
    List<ApuestaIndividualModel> individuales(String bucket) =>
        ((json['apuestas_individuales'] as Map<String, dynamic>? ?? {})[bucket] as List? ?? [])
            .map((a) => ApuestaIndividualModel.fromJson(a))
            .toList();
    List<CombinadaMismoPartidoModel> combinadas(String bucket) =>
        ((json['combinadas_mismo_partido'] as Map<String, dynamic>? ?? {})[bucket] as List? ?? [])
            .map((c) => CombinadaMismoPartidoModel.fromJson(c))
            .toList();
    List<ParlaySugeridoModel> parlays(String bucket) =>
        ((json['parlays_sugeridos'] as Map<String, dynamic>? ?? {})[bucket] as List? ?? [])
            .map((p) => ParlaySugeridoModel.fromJson(p))
            .toList();

    return RecomendadasModel(
      fecha: json['fecha'] ?? '',
      individualesFijas: individuales('fijas'),
      individualesSonadoras: individuales('sonadoras'),
      combinadasFijas: combinadas('fijas'),
      combinadasSonadoras: combinadas('sonadoras'),
      parlaysFijas: parlays('fijas'),
      parlaysSonadoras: parlays('sonadoras'),
    );
  }
}
