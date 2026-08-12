import '../repositories/partido_repository.dart';
import '../entities/prediccion.dart';
import '../../core/errors/failures.dart';

class GetPrediccionEnVivo {
  final PartidoRepository _repository;
  const GetPrediccionEnVivo(this._repository);

  Future<({PrediccionEnVivo? prediccion, Failure? error})>
  call(int partidoId) => _repository.getPrediccionEnVivo(partidoId);
}
