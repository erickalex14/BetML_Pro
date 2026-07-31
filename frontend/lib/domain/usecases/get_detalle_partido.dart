import '../repositories/partido_repository.dart';
import '../entities/partido.dart';
import '../../core/errors/failures.dart';

class GetDetallePartido {
  final PartidoRepository _repository;
  const GetDetallePartido(this._repository);

  Future<({Partido? partido, Failure? error})>
  call(int id) => _repository.getDetalle(id);

}