import '../../domain/entities/analisis_avanzado.dart';

class MercadoPortafolioModel extends MercadoPortafolio {
  const MercadoPortafolioModel({
    required super.nombre,
    required super.cuota,
    required super.probabilidad,
    required super.stakePct,
  });

  factory MercadoPortafolioModel.fromJson(Map<String, dynamic> json) {
    return MercadoPortafolioModel(
      nombre: json['mercado'] ?? '',
      cuota: (json['cuota'] ?? 0.0).toDouble(),
      probabilidad: (json['probabilidad'] ?? 0.0).toDouble(),
      stakePct: (json['stake_pct'] ?? 0.0).toDouble(),
    );
  }
}

class KellyPortafolioModel extends KellyPortafolio {
  const KellyPortafolioModel({
    required super.mercados,
    required super.stakeTotalPct,
    required super.stakeTotalUnidades,
    required super.evPortafolio,
    required super.probabilidadRuina,
  });

  factory KellyPortafolioModel.fromJson(Map<String, dynamic> json) {
    final portafolio = json['portafolio'] as Map<String, dynamic>;
    return KellyPortafolioModel(
      mercados: (portafolio['mercados'] as List? ?? [])
          .map((m) => MercadoPortafolioModel.fromJson(m))
          .toList(),
      stakeTotalPct: (portafolio['stake_total_pct'] ?? 0.0).toDouble(),
      stakeTotalUnidades: (json['stake_total_unidades'] ?? 0.0).toDouble(),
      evPortafolio: (portafolio['ev_portafolio'] ?? 0.0).toDouble(),
      probabilidadRuina: (json['probabilidad_ruina_temporada'] ?? 0.0).toDouble(),
    );
  }
}

class JugadorMercadoModel extends JugadorMercado {
  const JugadorMercadoModel({
    required super.nombre,
    super.posicion,
    required super.nPartidosHistorial,
    required super.tirosPromedio,
    required super.tirosArcoPromedio,
    required super.probAnota,
    required super.probAmarilla,
    required super.probRoja,
    required super.tirosOverUnder,
  });

  factory JugadorMercadoModel.fromJson(Map<String, dynamic> json) {
    final tiros = json['tiros'] as Map<String, dynamic>? ?? {};
    final tirosArco = json['tiros_arco'] as Map<String, dynamic>? ?? {};
    final overUnder = tiros['over_under'] as Map<String, dynamic>? ?? {};
    return JugadorMercadoModel(
      nombre: json['nombre'] ?? 'Jugador',
      posicion: json['posicion'] as String?,
      nPartidosHistorial: json['n_partidos_historial'] ?? 0,
      tirosPromedio: (tiros['promedio'] ?? 0.0).toDouble(),
      tirosArcoPromedio: (tirosArco['promedio'] ?? 0.0).toDouble(),
      probAnota: (json['prob_anota'] ?? 0.0).toDouble(),
      probAmarilla: (json['prob_amarilla'] ?? 0.0).toDouble(),
      probRoja: (json['prob_roja'] ?? 0.0).toDouble(),
      tirosOverUnder: overUnder.map((k, v) => MapEntry(k, (v as num).toDouble())),
    );
  }
}

class JugadoresPartidoModel extends JugadoresPartido {
  const JugadoresPartidoModel({required super.local, required super.visitante});

  factory JugadoresPartidoModel.fromJson(Map<String, dynamic> json) {
    final jugadores = json['jugadores'] as Map<String, dynamic>;
    List<JugadorMercadoModel> parsear(String lado) =>
        (jugadores[lado] as List? ?? [])
            .map((j) => JugadorMercadoModel.fromJson(j))
            .toList();
    return JugadoresPartidoModel(
      local: parsear('local'),
      visitante: parsear('visitante'),
    );
  }
}
