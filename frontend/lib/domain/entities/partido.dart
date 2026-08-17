import 'prediccion.dart';


class Partido {
  final int       id;
  final String    liga;
  final int       ligaId;
  final String    local;
  final int       localId;
  final String?   localLogo;
  final String    visitante;
  final int       visitanteId;
  final String?   visitanteLogo;
  final DateTime  fecha;
  final String    estado;
  final int?      minuto;
  final int?      golesLocal;
  final int?      golesVisit;
  final int       temporada;
  final String?   jornada;
  final Prediccion? prediccion;
  final DisponibilidadPrediccion? disponibilidadPrediccion;

  const Partido({
    required this.id,
    required this.liga,
    required this.ligaId,
    required this.local,
    required this.localId,
    this.localLogo,
    required this.visitante,
    required this.visitanteId,
    this.visitanteLogo,
    required this.fecha,
    required this.estado,
    this.minuto,
    this.golesLocal,
    this.golesVisit,
    required this.temporada,
    this.jornada,
    this.prediccion,
    this.disponibilidadPrediccion,
  });

  // lógica pura del dominio
  String get hora =>
    '${fecha.hour.toString().padLeft(2,'0')}:${fecha.minute.toString().padLeft(2,'0')}';

  static const _meses = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];

  // "12 ago 2026 · 17:00" — fecha ya viene en hora local (America/Guayaquil,
  // ver backend/pipeline/config.py ahora_partidos()), sin conversión acá.
  String get fechaHoraLarga =>
    '${fecha.day} ${_meses[fecha.month - 1]} ${fecha.year} · $hora';

  bool get terminado    => estado == 'FT';
  bool get enJuego      => ['1H','HT','2H','ET'].contains(estado);
  bool get noComen      => estado == 'NS' || estado == 'TBD';
  bool get tienePred    => prediccion != null;

  String get marcador =>
    terminado || golesLocal != null
      ? '${golesLocal ?? 0} - ${golesVisit ?? 0}'
      : hora;

  // Etiqueta corta para el badge EN VIVO — minuto real de API-Football
  // si ya llegó, si no cae a HT/ET genérico (todavía no hay elapsed).
  String get minutoTexto {
    if (estado == 'HT') return 'Descanso';
    if (minuto != null) return "$minuto'";
    return estado;
  }
}

class DisponibilidadPrediccion {
  final String codigo;
  final String calidad;
  final int localPartidosLocalia;
  final int visitantePartidosLocalia;
  final int localPartidosGenerales;
  final int visitantePartidosGenerales;

  const DisponibilidadPrediccion({
    required this.codigo,
    required this.calidad,
    required this.localPartidosLocalia,
    required this.visitantePartidosLocalia,
    required this.localPartidosGenerales,
    required this.visitantePartidosGenerales,
  });
}
