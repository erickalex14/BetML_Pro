import '../../domain/entities/partido.dart';
import '../../domain/entities/prediccion.dart';

// Model extiende Entity y agrega fromJson/toJson
// La entity no sabe nada de JSON — el model sí

class PartidoModel extends Partido {
  const PartidoModel({
    required super.id,
    required super.liga,
    required super.ligaId,
    required super.local,
    required super.localId,
    required super.visitante,
    required super.visitanteId,
    required super.fecha,
    required super.estado,
    super.golesLocal,
    super.golesVisit,
    required super.temporada,
    super.jornada,
    super.prediccion,
  });

  factory PartidoModel.fromJson(Map<String, dynamic> json) {
    return PartidoModel(
      id:           json['id'] as int,
      liga:         json['liga'] ?? 'Desconocida',
      ligaId:       json['liga_id'] ?? 0,
      local:        json['local'] ?? 'Local',
      localId:      json['local_id'] ?? 0,
      visitante:    json['visitante'] ?? 'Visitante',
      visitanteId:  json['visitante_id'] ?? 0,
      fecha:        DateTime.tryParse(json['fecha'] ?? '') ?? DateTime.now(),
      estado:       json['estado'] ?? 'NS',
      golesLocal:   json['goles_local'] as int?,
      golesVisit:   json['goles_visit'] as int?,
      temporada:    json['temporada'] ?? 2024,
      jornada:      json['jornada'] as String?,
      prediccion:   json['prediccion'] != null
                    ? PrediccionModel.fromJson(json['prediccion'])
                    : null,
    );
  }
}

class PrediccionModel extends Prediccion {
  const PrediccionModel({
    required super.partidoId,
    required super.probLocal,
    required super.probEmpate,
    required super.probVisitante,
    required super.resultado,
    required super.confianza,
    required super.mercados,
  });

  factory PrediccionModel.fromJson(Map<String, dynamic> json) {
    return PrediccionModel(
      partidoId:     json['partido_id'] ?? 0,
      probLocal:     (json['prob_local'] ?? 0.0).toDouble(),
      probEmpate:    (json['prob_empate'] ?? 0.0).toDouble(),
      probVisitante: (json['prob_visitante'] ?? 0.0).toDouble(),
      resultado:     json['prediccion'] ?? '',
      confianza:     (json['confianza'] ?? 0.0).toDouble(),
      mercados:      (json['mercados_recomendados'] as List? ?? [])
                     .map((m) => MercadoModel.fromJson(m))
                     .toList(),
    );
  }
}

class MercadoModel extends Mercado {
  const MercadoModel({
    required super.mercado,
    required super.seleccion,
    required super.probabilidad,
  });

  factory MercadoModel.fromJson(Map<String, dynamic> json) {
    return MercadoModel(
      mercado:      json['mercado'] ?? '',
      seleccion:    json['seleccion'] ?? '',
      probabilidad: (json['probabilidad'] ?? 0.0).toDouble(),
    );
  }
}

class StatsModeloModel extends StatsModelo {
  const StatsModeloModel({
    required super.total,
    required super.acertadas,
    required super.falladas,
    required super.pendientes,
    super.accuracy,
  });

  factory StatsModeloModel.fromJson(Map<String, dynamic> json) {
    return StatsModeloModel(
      total:      json['total'] ?? 0,
      acertadas:  json['acertadas'] ?? 0,
      falladas:   json['falladas'] ?? 0,
      pendientes: json['pendientes'] ?? 0,
      accuracy:   json['accuracy'] != null
                  ? (json['accuracy'] as num).toDouble()
                  : null,
    );
  }
}