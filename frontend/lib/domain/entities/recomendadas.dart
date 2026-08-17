// Apuesta individual recomendada — la mejor value bet de un mercado,
// de cualquier partido de hoy, ordenadas por EV. Mismos campos que
// KellyMercado (analisis_avanzado.dart) más el partido al que pertenece
// — son conceptos relacionados pero vienen de un endpoint distinto
// (agregado sobre TODOS los partidos, no uno solo), entidad propia.
class ApuestaIndividual {
  final int partidoId;
  final String local;
  final String visitante;
  final String? localLogo;
  final String? visitanteLogo;
  final String liga;
  final int? ligaId;
  final DateTime? hora;
  final String mercado;
  final double probabilidad;
  final double cuota;
  final double ev;
  final double edge;
  final double stakePct;

  /// null = todavía sin resolver. Se llena cuando el partido termina y
  /// job_cerrar_predicciones la cierra contra el resultado real.
  final bool? acerto;
  final String? estadoPartido;

  const ApuestaIndividual({
    required this.partidoId,
    required this.local,
    required this.visitante,
    this.localLogo,
    this.visitanteLogo,
    required this.liga,
    this.ligaId,
    this.hora,
    required this.mercado,
    required this.probabilidad,
    required this.cuota,
    required this.ev,
    required this.edge,
    required this.stakePct,
    this.acerto,
    this.estadoPartido,
  });

  bool get resuelta => acerto != null;
  bool get enJuego => ['1H', 'HT', '2H', 'ET'].contains(estadoPartido);

  String get porQue =>
      'Probabilidad del modelo ${(probabilidad * 100).toStringAsFixed(0)}% '
      'vs cuota ${cuota.toStringAsFixed(2)} → edge ${(edge * 100).toStringAsFixed(1)}pp';
}

class PronosticoJugador {
  final int partidoId;
  final String local;
  final String visitante;
  final String? localLogo;
  final String? visitanteLogo;
  final String liga;
  final String clave;
  final String mercado;
  final String jugador;
  final double probabilidad;
  final int nPartidosHistorial;
  final bool? acerto;

  const PronosticoJugador({
    required this.partidoId,
    required this.local,
    required this.visitante,
    this.localLogo,
    this.visitanteLogo,
    required this.liga,
    required this.clave,
    required this.mercado,
    required this.jugador,
    required this.probabilidad,
    required this.nPartidosHistorial,
    this.acerto,
  });
}

class MercadoCombinada {
  final String nombre;
  final double cuota;
  final double probabilidad;
  final double stakePct;

  const MercadoCombinada({
    required this.nombre,
    required this.cuota,
    required this.probabilidad,
    required this.stakePct,
  });
}

class CombinadaMismoPartido {
  final int partidoId;
  final String local;
  final String visitante;
  final String liga;
  final List<MercadoCombinada> mercados;
  final double stakeTotalPct;
  final double evPortafolio;

  const CombinadaMismoPartido({
    required this.partidoId,
    required this.local,
    required this.visitante,
    required this.liga,
    required this.mercados,
    required this.stakeTotalPct,
    required this.evPortafolio,
  });
}

class PataParlay {
  final int partidoId;
  final String local;
  final String visitante;
  final String mercado;

  const PataParlay({
    required this.partidoId,
    required this.local,
    required this.visitante,
    required this.mercado,
  });
}

class ParlaySugerido {
  final int nPatas;
  final List<PataParlay> selecciones;
  final double probCombinada;
  final double cuotaCombinada;
  final double stakePct;
  final double ev;

  const ParlaySugerido({
    required this.nPatas,
    required this.selecciones,
    required this.probCombinada,
    required this.cuotaCombinada,
    required this.stakePct,
    required this.ev,
  });
}

// "fijas" = alta probabilidad del modelo, para apostar con poco riesgo.
// "sonadoras" = cuota alta / probabilidad menor y mayor riesgo —
// ambas siguen siendo value bets con edge positivo, no apuestas al azar
// (ver UMBRAL_FIJA_PROB en backend/api/routes/predicciones.py).
class Recomendadas {
  final String fecha;
  final List<ApuestaIndividual> individualesFijas;
  final List<ApuestaIndividual> individualesSonadoras;
  final List<PronosticoJugador> jugadoresFijas;
  final List<PronosticoJugador> jugadoresSonadoras;
  final List<CombinadaMismoPartido> combinadasFijas;
  final List<CombinadaMismoPartido> combinadasSonadoras;
  final List<ParlaySugerido> parlaysFijas;
  final List<ParlaySugerido> parlaysSonadoras;

  const Recomendadas({
    required this.fecha,
    required this.individualesFijas,
    required this.individualesSonadoras,
    required this.jugadoresFijas,
    required this.jugadoresSonadoras,
    required this.combinadasFijas,
    required this.combinadasSonadoras,
    required this.parlaysFijas,
    required this.parlaysSonadoras,
  });

  bool get vacio =>
      individualesFijas.isEmpty &&
      individualesSonadoras.isEmpty &&
      jugadoresFijas.isEmpty &&
      jugadoresSonadoras.isEmpty &&
      combinadasFijas.isEmpty &&
      combinadasSonadoras.isEmpty &&
      parlaysFijas.isEmpty &&
      parlaysSonadoras.isEmpty;
}
