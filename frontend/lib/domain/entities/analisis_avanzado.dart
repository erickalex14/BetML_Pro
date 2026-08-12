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

// Mercado individual (no combinado en portafolio) — cubre 1X2, goles
// O/U, BTTS, corners, tarjetas, rojas, hándicap, 1er/2do tiempo, cada
// uno con su propio Kelly independiente. Distinto de MercadoPortafolio
// (que solo cubre los correlacionados vía Monte Carlo conjunto).
class KellyMercado {
  final String mercado;
  final String clave;
  final double probabilidad;
  final double cuota;
  final double ev;
  final double edge;
  final bool esValueBet;
  final double stakePct;
  final double stakeUnits;
  final double cuotaJusta;
  final double probImplicita;
  final String mensaje;

  const KellyMercado({
    required this.mercado,
    required this.clave,
    required this.probabilidad,
    required this.cuota,
    required this.ev,
    required this.edge,
    required this.esValueBet,
    required this.stakePct,
    required this.stakeUnits,
    required this.cuotaJusta,
    required this.probImplicita,
    required this.mensaje,
  });

  // texto trazable: de dónde sale el edge, no una afirmación sin números
  String get porQue =>
      'Probabilidad del modelo ${(probabilidad * 100).toStringAsFixed(0)}% '
      'vs ${(probImplicita * 100).toStringAsFixed(0)}% implícita por la cuota '
      '(${cuota.toStringAsFixed(2)}) → edge ${(edge * 100).toStringAsFixed(1)}pp';

  // Categoría por prefijo de clave — mismo vocabulario que
  // construir_lista_mercados() en el backend, no una lista aparte a
  // mantener sincronizada a mano.
  String get categoria {
    if (clave == 'local' || clave == 'empate' || clave == 'visitante') return 'Resultado del partido';
    if (clave.startsWith('handicap_')) return 'Hándicap';
    if (clave.startsWith('goles_1t_')) return 'Goles primer tiempo';
    if (clave.startsWith('goles_')) return 'Goles totales';
    if (clave.startsWith('btts_')) return 'Ambos equipos anotan';
    if (clave.startsWith('corners_')) return 'Córners';
    if (clave.startsWith('tarjetas_')) return 'Tarjetas';
    if (clave.startsWith('rojas_')) return 'Tarjetas rojas';
    if (clave.startsWith('1t_')) return 'Resultado primer tiempo';
    if (clave.startsWith('2t_')) return 'Resultado segundo tiempo';
    return 'Otros';
  }

  static const List<String> ordenCategorias = [
    'Resultado del partido', 'Hándicap', 'Goles totales', 'Ambos equipos anotan',
    'Córners', 'Tarjetas', 'Tarjetas rojas', 'Resultado primer tiempo',
    'Goles primer tiempo', 'Resultado segundo tiempo', 'Otros',
  ];
}

class KellyAnalisis {
  final List<KellyMercado> todosMercados;
  final int nValueBets;

  const KellyAnalisis({required this.todosMercados, required this.nValueBets});
}

class JugadorMercado {
  final String nombre;
  final String? posicion;
  final int nPartidosHistorial;
  final double tirosPromedio;
  final double tirosArcoPromedio;
  final double asistenciasPromedio;
  final double pasesPromedio;
  final double entradasPromedio;
  final double probAnota;
  final double probAmarilla;
  final double probRoja;
  // clave "over_0_5" -> probabilidad, ya vienen listas del backend
  final Map<String, double> tirosOverUnder;
  final Map<String, double> tirosArcoOverUnder;
  final Map<String, double> asistenciasOverUnder;
  final Map<String, double> pasesOverUnder;
  final Map<String, double> entradasOverUnder;
  final Map<String, double> golesOverUnder;

  const JugadorMercado({
    required this.nombre,
    this.posicion,
    required this.nPartidosHistorial,
    required this.tirosPromedio,
    required this.tirosArcoPromedio,
    required this.asistenciasPromedio,
    required this.pasesPromedio,
    required this.entradasPromedio,
    required this.probAnota,
    required this.probAmarilla,
    required this.probRoja,
    required this.tirosOverUnder,
    required this.tirosArcoOverUnder,
    required this.asistenciasOverUnder,
    required this.pasesOverUnder,
    required this.entradasOverUnder,
    required this.golesOverUnder,
  });

  // avatar sin foto real — inicial + color por línea de juego, no un
  // ícono genérico sin sentido
  String get inicial => nombre.isNotEmpty ? nombre[0].toUpperCase() : '?';
}

class JugadoresPartido {
  final List<JugadorMercado> local;
  final List<JugadorMercado> visitante;

  const JugadoresPartido({required this.local, required this.visitante});

  bool get vacio => local.isEmpty && visitante.isEmpty;
}
