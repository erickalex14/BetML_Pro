import '../../domain/entities/analisis_imagen.dart';

class SeleccionImagenModel extends SeleccionImagen {
  const SeleccionImagenModel({
    required super.mercado,
    required super.nombreLegible,
    required super.reconocido,
    super.aviso,
    super.probabilidad,
    super.cuotaDisponible,
    super.edge,
    super.recomendacion,
  });

  factory SeleccionImagenModel.fromJson(Map<String, dynamic> json) {
    return SeleccionImagenModel(
      mercado: json['mercado'] ?? '',
      nombreLegible: json['nombre_legible'] ?? json['mercado'] ?? '',
      reconocido: json['reconocido'] ?? false,
      aviso: json['aviso'] as String?,
      probabilidad: (json['probabilidad'] as num?)?.toDouble(),
      cuotaDisponible: (json['cuota_disponible'] as num?)?.toDouble(),
      edge: (json['edge'] as num?)?.toDouble(),
      recomendacion: json['recomendacion'] as String?,
    );
  }
}

class AnalisisImagenResultadoModel extends AnalisisImagenResultado {
  const AnalisisImagenResultadoModel({
    required super.reconocido,
    super.partidoId,
    required super.avisos,
    required super.sinReconocer,
    required super.selecciones,
    super.probCombinadaEstimada,
  });

  factory AnalisisImagenResultadoModel.fromJson(Map<String, dynamic> json) {
    return AnalisisImagenResultadoModel(
      reconocido: json['reconocido'] ?? false,
      partidoId: json['partido_id'] as int?,
      avisos: (json['avisos'] as List? ?? []).map((e) => e.toString()).toList(),
      sinReconocer: (json['sin_reconocer'] as List? ?? []).map((e) => e.toString()).toList(),
      selecciones: (json['selecciones'] as List? ?? [])
          .map((s) => SeleccionImagenModel.fromJson(s))
          .toList(),
      probCombinadaEstimada: (json['prob_combinada_estimada'] as num?)?.toDouble(),
    );
  }
}
