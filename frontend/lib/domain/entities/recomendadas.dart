// Apuesta individual recomendada — la mejor value bet de un mercado,
// de cualquier partido de hoy, ordenadas por EV. Mismos campos que
// KellyMercado (analisis_avanzado.dart) más el partido al que pertenece
// — son conceptos relacionados pero vienen de un endpoint distinto
// (agregado sobre TODOS los partidos, no uno solo), entidad propia.
class ApuestaIndividual {
  final int partidoId;
  final String local;
  final String visitante;
  final String liga;
  final String mercado;
  final double probabilidad;
  final double cuota;
  final double ev;
  final double edge;
  final double stakePct;

  const ApuestaIndividual({
    required this.partidoId,
    required this.local,
    required this.visitante,
    required this.liga,
    required this.mercado,
    required this.probabilidad,
    required this.cuota,
    required this.ev,
    required this.edge,
    required this.stakePct,
  });

  String get porQue =>
      'Probabilidad del modelo ${(probabilidad * 100).toStringAsFixed(0)}% '
      'vs cuota ${cuota.toStringAsFixed(2)} → edge ${(edge * 100).toStringAsFixed(1)}pp';
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

class Recomendadas {
  final String fecha;
  final List<ApuestaIndividual> apuestasIndividuales;
  final List<CombinadaMismoPartido> combinadasMismoPartido;
  final List<ParlaySugerido> parlaysSugeridos;

  const Recomendadas({
    required this.fecha,
    required this.apuestasIndividuales,
    required this.combinadasMismoPartido,
    required this.parlaysSugeridos,
  });

  bool get vacio =>
      apuestasIndividuales.isEmpty && combinadasMismoPartido.isEmpty && parlaysSugeridos.isEmpty;
}
