import '../entities/partido.dart';
import '../entities/prediccion.dart';
import '../entities/recomendadas.dart';
import '../../core/errors/failures.dart';

abstract class PartidoRepository {
  
  Future<({List<Partido> partidos, String fecha, Failure? error})>
    getPartidosHoy();
  
  Future<({Partido? partido, Failure? error})> 
    getDetalle(int id);

  Future<({StatsModelo? stats, Failure? error})>
    getStatsModelo();

  Future<({List<Prediccion> predicciones, Failure? error})>
    getPrediccionesHoy();

  Future<({List<PrediccionGuardada> predicciones, Failure? error})>
    getPrediccionesMias({String? estado});

  Future<({Recomendadas? recomendadas, Failure? error})>
    getRecomendadas();

  // null (sin error) si el partido no está en juego — estado normal,
  // no una falla de red/servidor.
  Future<({PrediccionEnVivo? prediccion, Failure? error})>
    getPrediccionEnVivo(int partidoId);
}
