class Prediccion {
  final int partidoId;
  final double probLocal;
  final double probEmpate;
  final double probVisitante;
  final String resultado;
  final double confianza;
  final List<Mercado> mercados;
  final List<Factor> factores;
  final String? resumenH2h;

  const Prediccion({
    required this.partidoId,
    required this.probLocal,
    required this.probEmpate,
    required this.probVisitante,
    required this.resultado,
    required this.confianza,
    required this.mercados,
    this.factores = const [],
    this.resumenH2h,
  });

  // Computed properties
  double get probMax =>
      [probLocal, probEmpate, probVisitante].reduce((a, b) => a > b ? a : b);

  bool get altaConfianza => confianza >= 0.65;

  List<Mercado> get mercadosTop =>
      mercados.where((m) => m.probabilidad >= 0.60).toList()
        ..sort((a, b) => b.probabilidad.compareTo(a.probabilidad));
}

// "favorece": "local" | "visitante" | "parejo" — mismo vocabulario que
// devuelve backend/models/explicacion.py, sin traducir a otra cosa acá.
class Factor {
  final String factor;
  final String favorece;
  final String texto;

  const Factor({required this.factor, required this.favorece, required this.texto});
}

class Mercado {
  final String mercado;
  final String seleccion;
  final double probabilidad;

  const Mercado({
    required this.mercado,
    required this.seleccion,
    required this.probabilidad,
  });

  String get label =>
      '$mercado: $seleccion · ${(probabilidad * 100).toStringAsFixed(0)}%';
}

// Un registro guardado (POST /guardar-mercados) — pendiente hasta que
// el partido termina y job_cerrar_predicciones.py lo resuelve.
class PrediccionGuardada {
  final int id;
  final int partidoId;
  final String? local;
  final String? visitante;
  final String? liga;
  final String mercado;
  final String prediccion;
  final double probabilidad;
  final String? resultadoReal;
  final bool? acerto; // null = pendiente
  final DateTime? creadoEn;

  const PrediccionGuardada({
    required this.id,
    required this.partidoId,
    this.local,
    this.visitante,
    this.liga,
    required this.mercado,
    required this.prediccion,
    required this.probabilidad,
    this.resultadoReal,
    this.acerto,
    this.creadoEn,
  });

  bool get pendiente => acerto == null;
}

class StatsModelo {
  final int total;
  final int acertadas;
  final int falladas;
  final int pendientes;
  final double? accuracy;

  const StatsModelo({
    required this.total,
    required this.acertadas,
    required this.falladas,
    required this.pendientes,
    this.accuracy,
  });

  String get accuracyStr => accuracy != null
      ? '${(accuracy! * 100).toStringAsFixed(1)}%'
      : 'Sin datos';
}
