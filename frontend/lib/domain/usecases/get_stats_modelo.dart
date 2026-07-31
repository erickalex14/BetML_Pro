import '../repositories/partido_repository.dart';
import '../entities/prediccion.dart';
import '../../core/errors/failures.dart';

class GetStatsModelo {
  final PartidoRepository _repository;
  const GetStatsModelo(this._repository);

  Future<({StatsModelo? stats, Failure? error})>
    call() => _repository.getStatsModelo();
}