import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../core/constants.dart';
import '../../core/errors/failures.dart';
import '../models/analisis_imagen_model.dart';

class AnalisisImagenRemoteDataSource {
  final http.Client _client;
  const AnalisisImagenRemoteDataSource(this._client);

  Future<AnalisisImagenResultadoModel> analizar(List<int> bytes, String nombreArchivo) async {
    try {
      final request = http.MultipartRequest(
          'POST', Uri.parse('${ApiConstants.baseUrl}${ApiConstants.analizarCaptura}'))
        ..files.add(http.MultipartFile.fromBytes('imagen', bytes, filename: nombreArchivo));

      final streamed = await _client.send(request).timeout(const Duration(seconds: 30));
      final response = await http.Response.fromStream(streamed);
      final data = json.decode(response.body) as Map<String, dynamic>;

      if (response.statusCode != 200) {
        throw ServerFailure((data['detail'] ?? 'Error del servidor').toString(), response.statusCode);
      }
      return AnalisisImagenResultadoModel.fromJson(data);
    } on Failure {
      rethrow;
    } catch (e) {
      throw NetworkFailure('Sin conexión: $e');
    }
  }
}
