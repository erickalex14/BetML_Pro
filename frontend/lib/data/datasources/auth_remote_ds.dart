import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../core/constants.dart';
import '../../core/errors/failures.dart';

class AuthTokens {
  final String access;
  final String refresh;
  const AuthTokens({required this.access, required this.refresh});
}

// Sin AuthClient a propósito — login/registro son los únicos endpoints
// públicos (main.py: "/auth queda abierto"), no hay token todavía que inyectar.
class AuthRemoteDataSource {
  final http.Client _client;
  const AuthRemoteDataSource(this._client);

  Future<AuthTokens> _postTokens(
      String endpoint, Map<String, dynamic> body) async {
    try {
      final response = await _client
          .post(
            Uri.parse('${ApiConstants.baseUrl}$endpoint'),
            headers: {'Content-Type': 'application/json'},
            body: json.encode(body),
          )
          .timeout(ApiConstants.timeout);

      final data = json.decode(response.body) as Map<String, dynamic>;

      if (response.statusCode == 200 || response.statusCode == 201) {
        return AuthTokens(
          access: data['access_token'] as String,
          refresh: data['refresh_token'] as String,
        );
      }
      throw ServerFailure(
          (data['detail'] ?? 'Error de autenticación').toString(),
          response.statusCode);
    } on ServerFailure {
      rethrow;
    } catch (e) {
      throw NetworkFailure('Sin conexión: $e');
    }
  }

  Future<AuthTokens> login(String email, String password) => _postTokens(
      ApiConstants.authLogin, {'email': email, 'password': password});

  Future<AuthTokens> registro(String email, String password) => _postTokens(
      ApiConstants.authRegistro, {'email': email, 'password': password});

  Future<AuthTokens> google(String idToken) =>
      _postTokens(ApiConstants.authGoogle, {'id_token': idToken});

  // A diferencia de login/registro, /auth/me SÍ requiere JWT — quien
  // instancie este datasource para llamar a me() debe pasar un
  // AuthClient en el constructor, no un http.Client() plano.
  Future<String> me() async {
    final response = await _client
        .get(Uri.parse('${ApiConstants.baseUrl}${ApiConstants.authMe}'))
        .timeout(ApiConstants.timeout);
    final data = json.decode(response.body) as Map<String, dynamic>;
    if (response.statusCode != 200) {
      throw ServerFailure(
          (data['detail'] ?? 'No se pudo cargar el perfil').toString(),
          response.statusCode);
    }
    return data['email'] as String;
  }
}
