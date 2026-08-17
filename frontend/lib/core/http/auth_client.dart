import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import '../auth_storage.dart';
import '../constants.dart';

// http.Client que inyecta el JWT guardado en cada request — todos los
// datasources (menos auth_remote_ds, que es público) usan este en vez
// de http.Client() directo, así ningún endpoint protegido queda sin
// header por olvido.
class AuthClient extends http.BaseClient {
  final http.Client _inner;
  static Future<bool>? _refreshEnCurso;
  AuthClient([http.Client? inner]) : _inner = inner ?? http.Client();

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final cuerpo = await request.finalize().toBytes();
    var respuesta = await _enviarCopia(request, cuerpo);
    if (respuesta.statusCode != 401 ||
        request.url.path.endsWith(ApiConstants.authRefresh)) {
      return respuesta;
    }

    _refreshEnCurso ??= _renovar().whenComplete(() => _refreshEnCurso = null);
    if (!await _refreshEnCurso!) return respuesta;
    return _enviarCopia(request, cuerpo);
  }

  Future<http.StreamedResponse> _enviarCopia(
      http.BaseRequest original, Uint8List cuerpo) async {
    final copia = http.Request(original.method, original.url)
      ..headers.addAll(original.headers)
      ..bodyBytes = cuerpo;
    final token = await AuthStorage.leerToken();
    if (token != null) {
      copia.headers['Authorization'] = 'Bearer $token';
    }
    return _inner.send(copia);
  }

  static Future<bool> _renovar() async {
    final refresh = await AuthStorage.leerRefresh();
    if (refresh == null) return false;
    try {
      final respuesta = await http
          .post(
            Uri.parse('${ApiConstants.baseUrl}${ApiConstants.authRefresh}'),
            headers: {
              'Content-Type': 'application/json',
              'X-BetML-Auth-Version': '2'
            },
            body: jsonEncode({'refresh_token': refresh}),
          )
          .timeout(ApiConstants.timeout);
      if (respuesta.statusCode != 200) throw Exception('refresh rechazado');
      final data = jsonDecode(respuesta.body) as Map<String, dynamic>;
      await AuthStorage.guardarTokens(
          data['access_token'], data['refresh_token']);
      return true;
    } catch (_) {
      await AuthStorage.borrarTokens();
      AuthStorage.alExpirarSesion?.call();
      return false;
    }
  }
}
