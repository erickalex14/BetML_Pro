import '../repositories/partido_repository.dart';
import '../entities/recomendadas.dart';
import '../../core/errors/failures.dart';

class GetRecomendadas {
  final PartidoRepository _repository;
  const GetRecomendadas(this._repository);

  Future<({Recomendadas? recomendadas, Failure? error})> call() => _repository.getRecomendadas();
}
