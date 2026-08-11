import '../../core/http/auth_client.dart';
import '../../core/errors/failures.dart';
import '../../domain/entities/analisis_avanzado.dart';
import '../../domain/repositories/analisis_repository.dart';
import '../datasources/analisis_remote_ds.dart';

class AnalisisRepositoryImpl implements AnalisisRepository {
  final AnalisisRemoteDataSource _dataSource;
  const AnalisisRepositoryImpl(this._dataSource);

  factory AnalisisRepositoryImpl.create() {
    return AnalisisRepositoryImpl(AnalisisRemoteDataSource(AuthClient()));
  }

  @override
  Future<({KellyPortafolio? portafolio, Failure? error})>
      getKellyPortafolio(int partidoId) async {
    try {
      final r = await _dataSource.getKellyPortafolio(partidoId);
      return (portafolio: r as KellyPortafolio, error: null);
    } on Failure catch (f) {
      return (portafolio: null, error: f);
    } catch (e) {
      return (portafolio: null, error: NetworkFailure(e.toString()));
    }
  }

  @override
  Future<({JugadoresPartido? jugadores, Failure? error})>
      getJugadores(int partidoId) async {
    try {
      final r = await _dataSource.getJugadores(partidoId);
      return (jugadores: r as JugadoresPartido, error: null);
    } on Failure catch (f) {
      return (jugadores: null, error: f);
    } catch (e) {
      return (jugadores: null, error: NetworkFailure(e.toString()));
    }
  }
}
