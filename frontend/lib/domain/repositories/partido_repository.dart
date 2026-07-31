import '../entities/partido.dart';
import '../entities/prediccion.dart';
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
}
