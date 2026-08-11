import '../repositories/analisis_repository.dart';
import '../entities/analisis_avanzado.dart';
import '../../core/errors/failures.dart';

class GetKellyPortafolio {
  final AnalisisRepository _repository;
  const GetKellyPortafolio(this._repository);

  Future<({KellyPortafolio? portafolio, Failure? error})>
      call(int partidoId) => _repository.getKellyPortafolio(partidoId);
}
