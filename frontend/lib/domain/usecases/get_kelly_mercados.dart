import '../repositories/analisis_repository.dart';
import '../entities/analisis_avanzado.dart';
import '../../core/errors/failures.dart';

class GetKellyMercados {
  final AnalisisRepository _repository;
  const GetKellyMercados(this._repository);

  Future<({KellyAnalisis? kelly, Failure? error})>
      call(int partidoId) => _repository.getKelly(partidoId);
}
