import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../core/constants.dart';
import '../../core/errors/failures.dart';
import '../models/partido_model.dart';
import '../models/recomendadas_model.dart';

class PartidoRemoteDataSource {
  final http.Client _client;

  // Inyección del cliente HTTP — facilita testing
  const PartidoRemoteDataSource(this._client);

  Future<Map<String, dynamic>> _get(String endpoint) async {
    try {
      final response = await _client
        .get(Uri.parse('${ApiConstants.baseUrl}$endpoint'))
        .timeout(ApiConstants.timeout);

      if (response.statusCode == 200) {
        return json.decode(response.body) as Map<String, dynamic>;
      } else if (response.statusCode == 404) {
        throw const NotFoundFailure('Recurso no encontrado');
      } else {
        throw ServerFailure(
          'Error del servidor', response.statusCode);
      }
    } on NotFoundFailure {
      rethrow;
    } on ServerFailure {
      rethrow;
    } catch (e) {
      throw NetworkFailure('Sin conexión: $e');
    }
  }

  Future<List<dynamic>> _getList(String endpoint) async {
    try {
      final response = await _client
        .get(Uri.parse('${ApiConstants.baseUrl}$endpoint'))
        .timeout(ApiConstants.timeout);

      if (response.statusCode == 200) {
        return json.decode(response.body) as List<dynamic>;
      }
      throw ServerFailure('Error del servidor', response.statusCode);
    } catch (e) {
      if (e is ServerFailure) rethrow;
      throw NetworkFailure('Sin conexión: $e');
    }
  }

  Future<({List<PartidoModel> partidos, String fecha})>
    getPartidosHoy() async {
    final data = await _get(ApiConstants.partidosHoy);
    final lista = (data['partidos'] as List)
      .map((p) => PartidoModel.fromJson(p))
      .toList();
      return (partidos: lista.cast<PartidoModel>(), fecha: (data['fecha'] ?? '') as String);
  }

  Future<PartidoModel> getDetalle(int id) async {
    final data = await _get('${ApiConstants.partido}/$id');
    return PartidoModel.fromJson(data);
  }

  // 422 = partido no está en juego (o falta el minuto todavía) — estado
  // esperado, no un error a mostrar, se devuelve null en vez de lanzar.
  Future<PrediccionEnVivoModel?> getPrediccionEnVivo(int partidoId) async {
    try {
      final data = await _get('/predicciones/$partidoId/en-vivo');
      return PrediccionEnVivoModel.fromJson(data);
    } on ServerFailure catch (f) {
      if (f.statusCode == 422) return null;
      rethrow;
    }
  }

  Future<List<PrediccionModel>> getPrediccionesHoy() async {
    final lista = await _getList(ApiConstants.prediccionesHoy);
    return lista.map((p) => PrediccionModel.fromJson(p)).toList();
  }

  Future<StatsModeloModel> getStatsModelo() async {
    final data = await _get(ApiConstants.statsModelo);
    return StatsModeloModel.fromJson(data);
  }

  Future<List<PrediccionGuardadaModel>> getPrediccionesMias({String? estado}) async {
    final query = estado != null ? '?estado=$estado' : '';
    final data = await _get('${ApiConstants.prediccionesMias}$query');
    return (data['predicciones'] as List)
        .map((p) => PrediccionGuardadaModel.fromJson(p))
        .toList();
  }

  // Escanea todos los partidos de hoy — más lento que el resto (unos
  // segundos), timeout propio en vez del genérico de 10s
  Future<RecomendadasModel> getRecomendadas() async {
    try {
      final response = await _client
          .get(Uri.parse('${ApiConstants.baseUrl}${ApiConstants.recomendadas}'))
          .timeout(const Duration(seconds: 30));
      if (response.statusCode == 200) {
        return RecomendadasModel.fromJson(json.decode(response.body) as Map<String, dynamic>);
      }
      throw ServerFailure('Error del servidor', response.statusCode);
    } catch (e) {
      if (e is ServerFailure) rethrow;
      throw NetworkFailure('Sin conexión: $e');
    }
  }
}