import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../../core/auth_storage.dart';
import '../../core/errors/failures.dart';
import '../../data/datasources/auth_remote_ds.dart';

// Sin repository/usecase de por medio a propósito — a diferencia de
// Partido (leído desde varias pantallas por varios usecases), el JWT
// SOLO lo maneja este provider; envolverlo en más capas no tendría
// otro consumidor que las use.
class AuthProvider extends ChangeNotifier {
  final _dataSource = AuthRemoteDataSource(http.Client());

  String? _token;
  bool _cargando = true; // true al boot: todavía no sabemos si hay sesión
  String? _error;

  bool get autenticado => _token != null;
  bool get cargando => _cargando;
  String? get error => _error;

  AuthProvider() {
    _cargarSesion();
  }

  Future<void> _cargarSesion() async {
    _token = await AuthStorage.leerToken();
    _cargando = false;
    notifyListeners();
  }

  Future<bool> login(String email, String password) =>
      _autenticar(() => _dataSource.login(email, password));

  Future<bool> registro(String email, String password) =>
      _autenticar(() => _dataSource.registro(email, password));

  Future<bool> _autenticar(Future<String> Function() accion) async {
    _cargando = true;
    _error = null;
    notifyListeners();

    try {
      final token = await accion();
      await AuthStorage.guardarToken(token);
      _token = token;
      return true;
    } on Failure catch (f) {
      _error = f.mensaje;
      return false;
    } finally {
      _cargando = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await AuthStorage.borrarToken();
    _token = null;
    notifyListeners();
  }
}
