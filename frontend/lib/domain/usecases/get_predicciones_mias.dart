import '../repositories/partido_repository.dart';
import '../entities/prediccion.dart';
import '../../core/errors/failures.dart';

class GetPrediccionesMias {
  final PartidoRepository _repository;
  const GetPrediccionesMias(this._repository);

  Future<({List<PrediccionGuardada> predicciones, Failure? error})>
      call({String? estado}) => _repository.getPrediccionesMias(estado: estado);
}
