import '../../core/http/auth_client.dart';
import '../../domain/entities/partido.dart';
import '../../domain/entities/prediccion.dart';
import '../../domain/repositories/partido_repository.dart';
import '../../core/errors/failures.dart';
import '../datasources/partido_remote_ds.dart';

class PartidoRepositoryImpl implements PartidoRepository {
  final PartidoRemoteDataSource _dataSource;

  const PartidoRepositoryImpl(this._dataSource);

  // Factory — crea la instancia con el cliente HTTP autenticado (todos
  // estos endpoints están bajo JWT, ver backend/api/main.py)
  factory PartidoRepositoryImpl.create() {
    return PartidoRepositoryImpl(
      PartidoRemoteDataSource(AuthClient()),
    );
  }

  @override
  Future<({List<Partido> partidos, String fecha, Failure? error})>
    getPartidosHoy() async {
    try {
      final result = await _dataSource.getPartidosHoy();
      return (
        partidos: result.partidos as List<Partido>,
        fecha:    result.fecha,
        error:    null,
      );
    } on Failure catch (f) {
      return (partidos: <Partido>[], fecha: '', error: f);
    } catch (e) {
      return (
        partidos: <Partido>[],
        fecha: '',
        error: NetworkFailure(e.toString()),
      );
    }
  }

  @override
  Future<({Partido? partido, Failure? error})>
    getDetalle(int id) async {
    try {
      final partido = await _dataSource.getDetalle(id);
      return (partido: partido as Partido, error: null);
    } on Failure catch (f) {
      return (partido: null, error: f);
    } catch (e) {
      return (partido: null, error: NetworkFailure(e.toString()));
    }
  }

  @override
  Future<({List<Prediccion> predicciones, Failure? error})>
    getPrediccionesHoy() async {
    try {
      final lista = await _dataSource.getPrediccionesHoy();
      return (
        predicciones: lista as List<Prediccion>,
        error: null,
      );
    } on Failure catch (f) {
      return (predicciones: <Prediccion>[], error: f);
    } catch (e) {
      return (
        predicciones: <Prediccion>[],
        error: NetworkFailure(e.toString()),
      );
    }
  }

  @override
  Future<({StatsModelo? stats, Failure? error})>
    getStatsModelo() async {
    try {
      final stats = await _dataSource.getStatsModelo();
      return (stats: stats as StatsModelo, error: null);
    } on Failure catch (f) {
      return (stats: null, error: f);
    } catch (e) {
      return (stats: null, error: NetworkFailure(e.toString()));
    }
  }
}