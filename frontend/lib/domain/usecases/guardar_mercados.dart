import '../repositories/analisis_repository.dart';
import '../../core/errors/failures.dart';

class GuardarMercados {
  final AnalisisRepository _repository;
  const GuardarMercados(this._repository);

  Future<({List<String>? guardados, Failure? error})>
      call(int partidoId, List<String> claves) => _repository.guardarMercados(partidoId, claves);
}
