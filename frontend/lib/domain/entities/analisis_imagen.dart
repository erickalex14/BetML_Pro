class SeleccionImagen {
  final String mercado;
  final String nombreLegible;
  final bool reconocido;
  final String? aviso;
  final double? probabilidad;
  final double? cuotaDisponible;
  final double? edge;
  final String? recomendacion;

  const SeleccionImagen({
    required this.mercado,
    required this.nombreLegible,
    required this.reconocido,
    this.aviso,
    this.probabilidad,
    this.cuotaDisponible,
    this.edge,
    this.recomendacion,
  });
}

class AnalisisImagenResultado {
  final bool reconocido;
  final int? partidoId;
  final List<String> avisos;
  final List<String> sinReconocer;
  final List<SeleccionImagen> selecciones;
  final double? probCombinadaEstimada;

  const AnalisisImagenResultado({
    required this.reconocido,
    this.partidoId,
    required this.avisos,
    required this.sinReconocer,
    required this.selecciones,
    this.probCombinadaEstimada,
  });
}
