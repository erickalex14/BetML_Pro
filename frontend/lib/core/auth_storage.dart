import 'package:flutter_secure_storage/flutter_secure_storage.dart';

// Un solo lugar que sabe leer/guardar el JWT — AuthProvider y AuthClient
// comparten esta clave en vez de cada uno reinventar el storage.
class AuthStorage {
  static const _claveToken = 'jwt';
  static const _storage = FlutterSecureStorage();

  static Future<void> guardarToken(String token) =>
      _storage.write(key: _claveToken, value: token);

  static Future<String?> leerToken() => _storage.read(key: _claveToken);

  static Future<void> borrarToken() => _storage.delete(key: _claveToken);
}
