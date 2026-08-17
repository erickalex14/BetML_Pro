import 'package:flutter_secure_storage/flutter_secure_storage.dart';

// Un solo lugar que sabe leer/guardar el JWT — AuthProvider y AuthClient
// comparten esta clave en vez de cada uno reinventar el storage.
class AuthStorage {
  static const _claveAccess = 'jwt';
  static const _claveRefresh = 'refresh_token';
  static const _storage = FlutterSecureStorage();
  static void Function()? alExpirarSesion;

  static Future<void> guardarTokens(String access, String refresh) async {
    await _storage.write(key: _claveAccess, value: access);
    await _storage.write(key: _claveRefresh, value: refresh);
  }

  static Future<String?> leerToken() => _storage.read(key: _claveAccess);
  static Future<String?> leerRefresh() => _storage.read(key: _claveRefresh);

  static Future<void> borrarTokens() async {
    await _storage.delete(key: _claveAccess);
    await _storage.delete(key: _claveRefresh);
  }
}
