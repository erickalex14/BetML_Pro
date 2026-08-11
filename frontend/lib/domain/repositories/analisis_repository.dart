import '../entities/analisis_avanzado.dart';
import '../../core/errors/failures.dart';

abstract class AnalisisRepository {
  Future<({KellyPortafolio? portafolio, Failure? error})>
      getKellyPortafolio(int partidoId);

  Future<({JugadoresPartido? jugadores, Failure? error})>
      getJugadores(int partidoId);
}
