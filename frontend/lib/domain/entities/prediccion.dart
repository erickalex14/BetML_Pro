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
  final String calidadDatos;

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
    this.calidadDatos = 'alta',
  });

  // Computed properties
  double get probMax =>
      [probLocal, probEmpate, probVisitante].reduce((a, b) => a > b ? a : b);

  bool get altaConfianza => confianza >= 0.65;

  List<Mercado> get mercadosTop =>
      mercados.where((m) => m.probabilidad >= 0.60).toList()
        ..sort((a, b) => b.probabilidad.compareTo(a.probabilidad));
}

// Recalculo EN VIVO — GET /predicciones/{id}/en-vivo. Distinto de
// Prediccion (esa es pre-partido): esta ya suma el marcador actual y
// escala el xG por el tiempo que falta.
class MercadoEnVivo {
  final String mercado;
  final String clave;
  final double probabilidad;

  const MercadoEnVivo({
    required this.mercado,
    required this.clave,
    required this.probabilidad,
  });
}

class PrediccionEnVivo {
  final double probLocal;
  final double probEmpate;
  final double probVisitante;
  final String marcadorActual;
  final int? minuto;
  final double fraccionRestante;
  final double golesEsperadosRestantes;
  final List<MercadoEnVivo> mercados;

  const PrediccionEnVivo({
    required this.probLocal,
    required this.probEmpate,
    required this.probVisitante,
    required this.marcadorActual,
    this.minuto,
    required this.fraccionRestante,
    this.golesEsperadosRestantes = 0,
    this.mercados = const [],
  });
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
  final String? localLogo;
  final String? visitanteLogo;
  final String? liga;
  final String? estado;
  final int? golesLocal;
  final int? golesVisit;
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
    this.localLogo,
    this.visitanteLogo,
    this.liga,
    this.estado,
    this.golesLocal,
    this.golesVisit,
    required this.mercado,
    required this.prediccion,
    required this.probabilidad,
    this.resultadoReal,
    this.acerto,
    this.creadoEn,
  });

  bool get pendiente => acerto == null;
  bool get terminado => estado == 'FT';
  bool get enJuego => ['1H', 'HT', '2H', 'ET'].contains(estado);

  String get marcador =>
      golesLocal != null ? '$golesLocal - ${golesVisit ?? 0}' : '';
}

// Predicciones de UN partido, agrupadas — la pantalla "Mis
// predicciones" mostraba una tarjeta suelta por mercado, así que un
// partido con 4 mercados guardados ocupaba 4 filas repitiendo los
// mismos nombres de equipo.
class PrediccionesDePartido {
  final int partidoId;
  final String? local;
  final String? visitante;
  final String? localLogo;
  final String? visitanteLogo;
  final String? liga;
  final String? estado;
  final String marcador;
  final List<PrediccionGuardada> predicciones;

  const PrediccionesDePartido({
    required this.partidoId,
    this.local,
    this.visitante,
    this.localLogo,
    this.visitanteLogo,
    this.liga,
    this.estado,
    required this.marcador,
    required this.predicciones,
  });

  int get acertadas => predicciones.where((p) => p.acerto == true).length;
  int get falladas => predicciones.where((p) => p.acerto == false).length;
  int get pendientes => predicciones.where((p) => p.pendiente).length;
  bool get terminado => estado == 'FT';
  bool get enJuego => ['1H', 'HT', '2H', 'ET'].contains(estado);

  /// Agrupa conservando el orden en que vino cada partido.
  static List<PrediccionesDePartido> agrupar(List<PrediccionGuardada> todas) {
    final porPartido = <int, List<PrediccionGuardada>>{};
    for (final p in todas) {
      porPartido.putIfAbsent(p.partidoId, () => []).add(p);
    }
    return porPartido.entries.map((e) {
      final primera = e.value.first;
      return PrediccionesDePartido(
        partidoId: e.key,
        local: primera.local,
        visitante: primera.visitante,
        localLogo: primera.localLogo,
        visitanteLogo: primera.visitanteLogo,
        liga: primera.liga,
        estado: primera.estado,
        marcador: primera.marcador,
        predicciones: e.value,
      );
    }).toList();
  }
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
