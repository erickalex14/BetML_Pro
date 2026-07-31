import 'package:flutter/material.dart';
import '../../domain/entities/prediccion.dart';
import '../../domain/usecases/get_stats_modelo.dart';
import '../../data/repositories/partido_repo_impl.dart';

class StatsProvider extends ChangeNotifier {
  late final GetStatsModelo _getStats;

  StatsModelo? _stats;
  bool _cargando = false;
  String? _error;

  StatsProvider() {
    _getStats = GetStatsModelo(PartidoRepositoryImpl.create());
  }

  StatsModelo? get stats => _stats;
  bool get cargando => _cargando;
  String? get error => _error;

  Future<void> cargar() async {
    _cargando = true;
    _error = null;
    notifyListeners();

    final result = await _getStats();

    if (result.error != null) {
      _error = result.error!.mensaje;
    } else {
      _stats = result.stats;
    }

    _cargando = false;
    notifyListeners();
  }
}
