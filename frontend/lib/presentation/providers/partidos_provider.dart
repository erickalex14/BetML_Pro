import 'package:flutter/material.dart';
import '../../domain/entities/partido.dart';
import '../../domain/usecases/get_partidos_hoy.dart';
import '../../data/repositories/partido_repo_impl.dart';

class PartidosProvider extends ChangeNotifier {
  // Use case inyectado — el provider no sabe de HTTP
  late final GetPartidosHoy _getPartidosHoy;

  List<Partido> _partidos      = [];
  String        _fecha         = '';
  bool          _cargando      = false;
  String?       _error;
  String?       _ligaFiltro;

  PartidosProvider() {
    // Inyección del use case con su repositorio
    _getPartidosHoy = GetPartidosHoy(
      PartidoRepositoryImpl.create()
    );
  }

  // Getters
  List<Partido> get partidos => _partidos;
  String        get fecha    => _fecha;
  bool          get cargando => _cargando;
  String?       get error    => _error;
  String?       get ligaFiltro => _ligaFiltro;

  List<Partido> get porLiga => _ligaFiltro == null
    ? _partidos
    : _partidos.where((p) => p.liga == _ligaFiltro).toList();

  List<String> get ligasDisponibles =>
    _partidos.map((p) => p.liga).toSet().toList()..sort();

  // Partidos con predicción de alta confianza
  List<Partido> get topPicks => _partidos
    .where((p) => p.tienePred && p.prediccion!.altaConfianza)
    .toList();

  void setFiltroLiga(String? liga) {
    _ligaFiltro = liga;
    notifyListeners();
  }

  // mostrarCargando=false — usado por el auto-refresh en background (cada
  // 60s en HomeScreen): la lista se actualiza sola cuando cambia el
  // marcador, sin tapar la pantalla con el skeleton cada vez.
  Future<void> cargarPartidosHoy({bool mostrarCargando = true}) async {
    if (mostrarCargando) {
      _cargando = true;
      _error    = null;
      notifyListeners();
    }

    final result = await _getPartidosHoy();

    if (result.error != null) {
      if (mostrarCargando) _error = result.error!.mensaje; // error silencioso en refresh de fondo, no tapa datos ya mostrados
    } else {
      _partidos = result.partidos;
      _fecha    = result.fecha;
    }

    _cargando = false;
    notifyListeners();
  }
}