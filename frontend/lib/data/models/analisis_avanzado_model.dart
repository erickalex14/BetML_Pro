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
      probabilidadRuina:
          (json['probabilidad_ruina_temporada'] ?? 0.0).toDouble(),
    );
  }
}

class KellyMercadoModel extends KellyMercado {
  const KellyMercadoModel({
    required super.mercado,
    required super.clave,
    required super.probabilidad,
    required super.cuota,
    required super.ev,
    required super.edge,
    required super.esValueBet,
    required super.stakePct,
    required super.stakeUnits,
    required super.cuotaJusta,
    required super.probImplicita,
    required super.mensaje,
    super.sinCuota,
  });

  factory KellyMercadoModel.fromJson(Map<String, dynamic> json) {
    return KellyMercadoModel(
      mercado: json['mercado'] ?? '',
      clave: json['clave'] ?? '',
      probabilidad: (json['probabilidad'] ?? 0.0).toDouble(),
      cuota: (json['cuota'] ?? 0.0).toDouble(),
      ev: (json['ev'] ?? 0.0).toDouble(),
      edge: (json['edge'] ?? 0.0).toDouble(),
      esValueBet: json['es_value_bet'] ?? false,
      stakePct: (json['stake_pct'] ?? 0.0).toDouble(),
      stakeUnits: (json['stake_units'] ?? 0.0).toDouble(),
      cuotaJusta: (json['cuota_justa'] ?? 0.0).toDouble(),
      probImplicita: (json['prob_implicita'] ?? 0.0).toDouble(),
      mensaje: json['mensaje'] ?? '',
      sinCuota: json['sin_cuota'] ?? false,
    );
  }
}

class KellyAnalisisModel extends KellyAnalisis {
  const KellyAnalisisModel(
      {required super.todosMercados, required super.nValueBets});

  factory KellyAnalisisModel.fromJson(Map<String, dynamic> json) {
    final kelly = json['kelly'] as Map<String, dynamic>;
    return KellyAnalisisModel(
      todosMercados: (kelly['todos_mercados'] as List? ?? [])
          .map((m) => KellyMercadoModel.fromJson(m))
          .toList(),
      nValueBets: kelly['n_value_bets'] ?? 0,
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
    required super.asistenciasPromedio,
    required super.pasesPromedio,
    required super.entradasPromedio,
    super.atajadasPromedio,
    required super.probAnota,
    required super.probAmarilla,
    required super.probRoja,
    required super.tirosOverUnder,
    required super.tirosArcoOverUnder,
    required super.asistenciasOverUnder,
    required super.pasesOverUnder,
    required super.entradasOverUnder,
    required super.golesOverUnder,
    super.atajadasOverUnder,
  });

  factory JugadorMercadoModel.fromJson(Map<String, dynamic> json) {
    Map<String, double> overUnderDe(String bloque) {
      final b = json[bloque] as Map<String, dynamic>? ?? {};
      final ou = b['over_under'] as Map<String, dynamic>? ?? {};
      return ou.map((k, v) => MapEntry(k, (v as num).toDouble()));
    }

    double promedioDe(String bloque) =>
        ((json[bloque] as Map<String, dynamic>? ?? {})['promedio'] ?? 0.0)
            .toDouble();

    return JugadorMercadoModel(
      nombre: json['nombre'] ?? 'Jugador',
      posicion: json['posicion'] as String?,
      nPartidosHistorial: json['n_partidos_historial'] ?? 0,
      tirosPromedio: promedioDe('tiros'),
      tirosArcoPromedio: promedioDe('tiros_arco'),
      asistenciasPromedio: promedioDe('asistencias'),
      pasesPromedio: promedioDe('pases'),
      entradasPromedio: promedioDe('entradas'),
      atajadasPromedio: promedioDe('atajadas'),
      probAnota: (json['prob_anota'] ?? 0.0).toDouble(),
      probAmarilla: (json['prob_amarilla'] ?? 0.0).toDouble(),
      probRoja: (json['prob_roja'] ?? 0.0).toDouble(),
      tirosOverUnder: overUnderDe('tiros'),
      tirosArcoOverUnder: overUnderDe('tiros_arco'),
      asistenciasOverUnder: overUnderDe('asistencias'),
      pasesOverUnder: overUnderDe('pases'),
      entradasOverUnder: overUnderDe('entradas'),
      golesOverUnder: overUnderDe('goles'),
      atajadasOverUnder: overUnderDe('atajadas'),
    );
  }
}

class JugadoresPartidoModel extends JugadoresPartido {
  const JugadoresPartidoModel({
    required super.local,
    required super.visitante,
    required super.mercados,
  });

  factory JugadoresPartidoModel.fromJson(Map<String, dynamic> json) {
    final jugadores = json['jugadores'] as Map<String, dynamic>;
    List<JugadorMercadoModel> parsear(String lado) =>
        (jugadores[lado] as List? ?? [])
            .map((j) => JugadorMercadoModel.fromJson(j))
            .toList();
    return JugadoresPartidoModel(
      local: parsear('local'),
      visitante: parsear('visitante'),
      mercados: (json['mercados'] as List? ?? [])
          .map((m) => MercadoJugadorDisponible(
                clave: m['clave'] ?? '',
                mercado: m['mercado'] ?? '',
                jugador: m['jugador'] ?? '',
                probabilidad: (m['probabilidad'] ?? 0).toDouble(),
                nPartidosHistorial: m['n_partidos_historial'] ?? 0,
              ))
          .toList(),
    );
  }
}
