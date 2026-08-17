import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:google_sign_in/google_sign_in.dart';
import '../../core/auth_storage.dart';
import '../../core/constants.dart';
import '../../core/http/auth_client.dart';
import '../../core/errors/failures.dart';
import '../../data/datasources/auth_remote_ds.dart';

// Sin repository/usecase de por medio a propósito — a diferencia de
// Partido (leído desde varias pantallas por varios usecases), el JWT
// SOLO lo maneja este provider; envolverlo en más capas no tendría
// otro consumidor que las use.
class AuthProvider extends ChangeNotifier {
  final _dataSource = AuthRemoteDataSource(http.Client());
  final _google = GoogleSignIn(
    serverClientId: ApiConstants.googleClientId.isEmpty
        ? null
        : ApiConstants.googleClientId,
  );

  String? _token;
  bool _cargando = true; // true al boot: todavía no sabemos si hay sesión
  String? _error;

  bool get autenticado => _token != null;
  bool get cargando => _cargando;
  String? get error => _error;

  AuthProvider() {
    AuthStorage.alExpirarSesion = () {
      _token = null;
      notifyListeners();
    };
    _cargarSesion();
  }

  Future<void> _cargarSesion() async {
    _token = await AuthStorage.leerToken();
    if (_token != null) {
      try {
        await AuthRemoteDataSource(AuthClient()).me();
        _token = await AuthStorage.leerToken();
      } catch (_) {
        await AuthStorage.borrarTokens();
        _token = null;
      }
    }
    _cargando = false;
    notifyListeners();
  }

  Future<bool> login(String email, String password) =>
      _autenticar(() => _dataSource.login(email, password));

  Future<bool> registro(String email, String password) =>
      _autenticar(() => _dataSource.registro(email, password));

  Future<bool> loginGoogle() => _autenticar(() async {
        final cuenta = await _google.signIn();
        if (cuenta == null) {
          throw const NetworkFailure('Inicio con Google cancelado');
        }
        final token = (await cuenta.authentication).idToken;
        if (token == null) {
          throw const NetworkFailure('Google no entregó un token válido');
        }
        return _dataSource.google(token);
      });

  Future<bool> _autenticar(Future<AuthTokens> Function() accion) async {
    _cargando = true;
    _error = null;
    notifyListeners();

    try {
      final tokens = await accion();
      await AuthStorage.guardarTokens(tokens.access, tokens.refresh);
      _token = tokens.access;
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
    final refresh = await AuthStorage.leerRefresh();
    if (refresh != null) {
      try {
        await http
            .post(
                Uri.parse('${ApiConstants.baseUrl}${ApiConstants.authLogout}'),
                headers: {'Content-Type': 'application/json'},
                body: '{"refresh_token":"$refresh"}')
            .timeout(ApiConstants.timeout);
      } catch (_) {}
    }
    await _google.signOut();
    await AuthStorage.borrarTokens();
    _token = null;
    notifyListeners();
  }
}
