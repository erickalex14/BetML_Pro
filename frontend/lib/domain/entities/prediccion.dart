class Prediccion {
  final int partidoId;
  final double probLocal;
  final double probEmpate;
  final double probVisitante;
  final String resultado;
  final double confianza;
  final List<Mercado> mercados;

  const Prediccion({
    required this.partidoId,
    required this.probLocal,
    required this.probEmpate,
    required this.probVisitante,
    required this.resultado,
    required this.confianza,
    required this.mercados,
  });

  // Computed properties
  double get probMax =>
      [probLocal, probEmpate, probVisitante].reduce((a, b) => a > b ? a : b);

  bool get altaConfianza => confianza >= 0.65;

  List<Mercado> get mercadosTop =>
      mercados.where((m) => m.probabilidad >= 0.60).toList()
        ..sort((a, b) => b.probabilidad.compareTo(a.probabilidad));
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
