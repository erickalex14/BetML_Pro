import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../core/constants.dart';
import '../../core/errors/failures.dart';
import '../../domain/entities/parlay.dart';
import '../models/parlay_model.dart';

class ParlayRemoteDataSource {
  final http.Client _client;
  const ParlayRemoteDataSource(this._client);

  Future<ParlayResultadoModel> calcular(List<ParlaySeleccionInput> selecciones,
      {double bankroll = 1000.0, double fraccion = 0.25, bool guardar = true}) async {
    try {
      final response = await _client
          .post(
            Uri.parse('${ApiConstants.baseUrl}${ApiConstants.combinada}'),
            headers: {'Content-Type': 'application/json'},
            body: json.encode({
              'selecciones': selecciones.map((s) => s.toJson()).toList(),
              'bankroll': bankroll,
              'fraccion': fraccion,
              'guardar': guardar,
            }),
          )
          .timeout(ApiConstants.timeout);

      final data = json.decode(response.body) as Map<String, dynamic>;
      if (response.statusCode != 200) {
        throw ServerFailure((data['detail'] ?? 'Error del servidor').toString(), response.statusCode);
      }
      return ParlayResultadoModel.fromJson(data);
    } on Failure {
      rethrow;
    } catch (e) {
      throw NetworkFailure('Sin conexión: $e');
    }
  }
}
