import '../repositories/analisis_repository.dart';
import '../entities/analisis_avanzado.dart';
import '../../core/errors/failures.dart';

class GetJugadoresPartido {
  final AnalisisRepository _repository;
  const GetJugadoresPartido(this._repository);

  Future<({JugadoresPartido? jugadores, Failure? error})>
      call(int partidoId) => _repository.getJugadores(partidoId);
}
