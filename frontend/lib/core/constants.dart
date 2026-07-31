class ApiConstants {
  static const String baseUrl = 'http://localhost:8070';

  static const String partidosHoy = '/partidos/hoy';
  static const String partido = '/partidos';
  static const String prediccionesHoy= '/predicciones/hoy';
  static const String statsModelo    = '/stats/modelo';

  //Timeout
  static const Duration timeout = Duration(seconds: 10);
}

class AppConstants {
  static const String appName = 'BetML Pro';
  static const String appVersion = '1.0.0';
  
  // Umbral mínimo para mostrar mercado recomendado
  static const double umbralMercado = 0.60;
}

