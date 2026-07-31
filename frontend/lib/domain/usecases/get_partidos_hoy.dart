import '../repositories/partido_repository.dart';
import '../entities/partido.dart';
import '../../core/errors/failures.dart';

class GetPartidosHoy {
  final  PartidoRepository _repository;

  const GetPartidosHoy(this._repository);

  Future<({List<Partido> partidos, String fecha, Failure? error})>
    call() => _repository.getPartidosHoy();
}