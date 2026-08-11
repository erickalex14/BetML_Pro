class MercadoPortafolio {
  final String nombre;
  final double cuota;
  final double probabilidad;
  final double stakePct;

  const MercadoPortafolio({
    required this.nombre,
    required this.cuota,
    required this.probabilidad,
    required this.stakePct,
  });
}

class KellyPortafolio {
  final List<MercadoPortafolio> mercados;
  final double stakeTotalPct;
  final double stakeTotalUnidades;
  final double evPortafolio;
  final double probabilidadRuina;

  const KellyPortafolio({
    required this.mercados,
    required this.stakeTotalPct,
    required this.stakeTotalUnidades,
    required this.evPortafolio,
    required this.probabilidadRuina,
  });

  bool get sinEdge => mercados.every((m) => m.stakePct == 0);
}

class JugadorMercado {
  final String nombre;
  final String? posicion;
  final int nPartidosHistorial;
  final double tirosPromedio;
  final double tirosArcoPromedio;
  final double probAnota;
  final double probAmarilla;
  final double probRoja;
  // clave "over_0_5" -> probabilidad, ya viene lista del backend
  final Map<String, double> tirosOverUnder;

  const JugadorMercado({
    required this.nombre,
    this.posicion,
    required this.nPartidosHistorial,
    required this.tirosPromedio,
    required this.tirosArcoPromedio,
    required this.probAnota,
    required this.probAmarilla,
    required this.probRoja,
    required this.tirosOverUnder,
  });
}

class JugadoresPartido {
  final List<JugadorMercado> local;
  final List<JugadorMercado> visitante;

  const JugadoresPartido({required this.local, required this.visitante});

  bool get vacio => local.isEmpty && visitante.isEmpty;
}
