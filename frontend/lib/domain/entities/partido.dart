import 'prediccion.dart';


class Partido {
  final int       id;
  final String    liga;
  final int       ligaId;
  final String    local;
  final int       localId;
  final String    visitante;
  final int       visitanteId;
  final DateTime  fecha;
  final String    estado;
  final int?      golesLocal;
  final int?      golesVisit;
  final int       temporada;
  final String?   jornada;
  final Prediccion? prediccion;

  const Partido({
    required this.id,
    required this.liga,
    required this.ligaId,
    required this.local,
    required this.localId,
    required this.visitante,
    required this.visitanteId,
    required this.fecha,
    required this.estado,
    this.golesLocal,
    this.golesVisit,
    required this.temporada,
    this.jornada,
    this.prediccion,
  });

  // lógica pura del dominio
  String get hora =>
    '${fecha.hour.toString().padLeft(2,'0')}:${fecha.minute.toString().padLeft(2,'0')}';

  bool get terminado    => estado == 'FT';
  bool get enJuego      => ['1H','HT','2H','ET'].contains(estado);
  bool get noComen      => estado == 'NS' || estado == 'TBD';
  bool get tienePred    => prediccion != null;

  String get marcador =>
    terminado || golesLocal != null
      ? '${golesLocal ?? 0} - ${golesVisit ?? 0}'
      : hora;
}