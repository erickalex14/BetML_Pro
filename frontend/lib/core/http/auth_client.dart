import 'package:http/http.dart' as http;
import '../auth_storage.dart';

// http.Client que inyecta el JWT guardado en cada request — todos los
// datasources (menos auth_remote_ds, que es público) usan este en vez
// de http.Client() directo, así ningún endpoint protegido queda sin
// header por olvido.
class AuthClient extends http.BaseClient {
  final http.Client _inner;
  AuthClient([http.Client? inner]) : _inner = inner ?? http.Client();

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final token = await AuthStorage.leerToken();
    if (token != null) {
      request.headers['Authorization'] = 'Bearer $token';
    }
    return _inner.send(request);
  }
}
