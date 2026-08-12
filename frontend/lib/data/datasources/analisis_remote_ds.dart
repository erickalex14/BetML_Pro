import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../core/constants.dart';
import '../../core/errors/failures.dart';
import '../models/analisis_avanzado_model.dart';

class AnalisisRemoteDataSource {
  final http.Client _client;
  const AnalisisRemoteDataSource(this._client);

  Future<Map<String, dynamic>> _get(String endpoint) async {
    try {
      final response = await _client
          .get(Uri.parse('${ApiConstants.baseUrl}$endpoint'))
          .timeout(ApiConstants.timeout);

      final data = json.decode(response.body) as Map<String, dynamic>;
      if (response.statusCode == 200) return data;
      if (response.statusCode == 404) {
        throw NotFoundFailure((data['detail'] ?? 'No encontrado').toString());
      }
      // 422 acá suele ser "sin cuotas guardadas" — mensaje real del backend,
      // más útil para el usuario que un genérico "error del servidor"
      throw ServerFailure(
          (data['detail'] ?? 'Error del servidor').toString(), response.statusCode);
    } on Failure {
      rethrow;
    } catch (e) {
      throw NetworkFailure('Sin conexión: $e');
    }
  }

  Future<KellyPortafolioModel> getKellyPortafolio(int partidoId,
      {double bankroll = 1000.0, double fraccion = 0.25}) async {
    final data = await _get(
        '${ApiConstants.kellyPortafolio(partidoId)}?bankroll=$bankroll&fraccion=$fraccion');
    return KellyPortafolioModel.fromJson(data);
  }

  Future<KellyAnalisisModel> getKelly(int partidoId, {double bankroll = 1000.0, double fraccion = 0.25}) async {
    final data = await _get('${ApiConstants.kelly(partidoId)}?bankroll=$bankroll&fraccion=$fraccion');
    return KellyAnalisisModel.fromJson(data);
  }

  Future<JugadoresPartidoModel> getJugadores(int partidoId) async {
    final data = await _get(ApiConstants.jugadores(partidoId));
    return JugadoresPartidoModel.fromJson(data);
  }

  // Guarda como Prediccion los mercados que el usuario eligió trackear
  // (no las value bets automáticas) — job_cerrar_predicciones.py los
  // cierra solo cuando el partido termine.
  Future<List<String>> guardarMercados(int partidoId, List<String> claves) async {
    try {
      final response = await _client
          .post(
            Uri.parse('${ApiConstants.baseUrl}${ApiConstants.guardarMercados(partidoId)}'),
            headers: {'Content-Type': 'application/json'},
            body: json.encode({'claves': claves}),
          )
          .timeout(ApiConstants.timeout);

      final data = json.decode(response.body) as Map<String, dynamic>;
      if (response.statusCode != 200) {
        throw ServerFailure((data['detail'] ?? 'Error del servidor').toString(), response.statusCode);
      }
      return (data['guardados'] as List).map((e) => e.toString()).toList();
    } on Failure {
      rethrow;
    } catch (e) {
      throw NetworkFailure('Sin conexión: $e');
    }
  }
}
