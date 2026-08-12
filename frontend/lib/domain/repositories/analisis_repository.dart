import '../entities/analisis_avanzado.dart';
import '../../core/errors/failures.dart';

abstract class AnalisisRepository {
  Future<({KellyPortafolio? portafolio, Failure? error})>
      getKellyPortafolio(int partidoId);

  Future<({KellyAnalisis? kelly, Failure? error})>
      getKelly(int partidoId);

  Future<({JugadoresPartido? jugadores, Failure? error})>
      getJugadores(int partidoId);

  Future<({List<String>? guardados, Failure? error})>
      guardarMercados(int partidoId, List<String> claves);
}
