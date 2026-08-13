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
    super.localLogo,
    required super.visitante,
    required super.visitanteId,
    super.visitanteLogo,
    required super.fecha,
    required super.estado,
    super.minuto,
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
      localLogo:    json['local_logo'] as String?,
      visitante:    json['visitante'] ?? 'Visitante',
      visitanteId:  json['visitante_id'] ?? 0,
      visitanteLogo: json['visitante_logo'] as String?,
      // El backend manda la fecha en UTC marcada con "Z"; toLocal() la
      // pasa a la zona del celular. Sin esto la hora salía 5 h tarde en
      // Ecuador (Pafos aparecía 17:00 jugándose 12:00).
      fecha:        (DateTime.tryParse(json['fecha'] ?? '') ?? DateTime.now()).toLocal(),
      estado:       json['estado'] ?? 'NS',
      minuto:       json['minuto'] as int?,
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
    super.factores,
    super.resumenH2h,
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
      factores:      (json['factores'] as List? ?? [])
                     .map((f) => FactorModel.fromJson(f))
                     .toList(),
      resumenH2h:    json['resumen_h2h'] as String?,
    );
  }
}

class PrediccionEnVivoModel extends PrediccionEnVivo {
  const PrediccionEnVivoModel({
    required super.probLocal,
    required super.probEmpate,
    required super.probVisitante,
    required super.marcadorActual,
    super.minuto,
    required super.fraccionRestante,
    super.golesEsperadosRestantes,
    super.mercados,
  });

  factory PrediccionEnVivoModel.fromJson(Map<String, dynamic> json) {
    return PrediccionEnVivoModel(
      probLocal:        (json['prob_local'] ?? 0.0).toDouble(),
      probEmpate:       (json['prob_empate'] ?? 0.0).toDouble(),
      probVisitante:    (json['prob_visitante'] ?? 0.0).toDouble(),
      marcadorActual:   json['marcador_actual'] ?? '0-0',
      minuto:           json['minuto'] as int?,
      fraccionRestante: (json['fraccion_restante'] ?? 0.0).toDouble(),
      golesEsperadosRestantes: (json['goles_esperados_restantes'] ?? 0.0).toDouble(),
      mercados: (json['mercados'] as List? ?? [])
          .map((m) => MercadoEnVivo(
                mercado: m['mercado'] ?? '',
                clave: m['clave'] ?? '',
                probabilidad: (m['probabilidad'] ?? 0.0).toDouble(),
              ))
          .toList(),
    );
  }
}

class FactorModel extends Factor {
  const FactorModel({required super.factor, required super.favorece, required super.texto});

  factory FactorModel.fromJson(Map<String, dynamic> json) {
    return FactorModel(
      factor:    json['factor'] ?? '',
      favorece:  json['favorece'] ?? 'parejo',
      texto:     json['texto'] ?? '',
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

class PrediccionGuardadaModel extends PrediccionGuardada {
  const PrediccionGuardadaModel({
    required super.id,
    required super.partidoId,
    super.local,
    super.visitante,
    super.localLogo,
    super.visitanteLogo,
    super.liga,
    super.estado,
    super.golesLocal,
    super.golesVisit,
    required super.mercado,
    required super.prediccion,
    required super.probabilidad,
    super.resultadoReal,
    super.acerto,
    super.creadoEn,
  });

  factory PrediccionGuardadaModel.fromJson(Map<String, dynamic> json) {
    return PrediccionGuardadaModel(
      id: json['id'] ?? 0,
      partidoId: json['partido_id'] ?? 0,
      local: json['local'] as String?,
      visitante: json['visitante'] as String?,
      localLogo: json['local_logo'] as String?,
      visitanteLogo: json['visitante_logo'] as String?,
      liga: json['liga'] as String?,
      estado: json['estado'] as String?,
      golesLocal: json['goles_local'] as int?,
      golesVisit: json['goles_visit'] as int?,
      mercado: json['mercado'] ?? '',
      prediccion: json['prediccion'] ?? '',
      probabilidad: (json['probabilidad'] ?? 0.0).toDouble(),
      resultadoReal: json['resultado_real'] as String?,
      acerto: json['acerto'] as bool?,
      creadoEn: json['creado_en'] != null ? DateTime.tryParse(json['creado_en']) : null,
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