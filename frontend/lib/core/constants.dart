class ApiConstants {
  // uvicorn default — backend/core/config.py no fija puerto propio
  static const String baseUrl = 'http://localhost:8000';

  static const String partidosHoy = '/partidos/hoy';
  static const String partido = '/partidos';
  static const String prediccionesHoy= '/predicciones/hoy';
  static const String statsModelo    = '/stats/modelo';

  static const String authLogin   = '/auth/login';
  static const String authRegistro = '/auth/registro';
  static const String authMe = '/auth/me';

  static String kellyPortafolio(int partidoId) => '/predicciones/$partidoId/kelly/portafolio';
  static String jugadores(int partidoId) => '/predicciones/$partidoId/jugadores';

  //Timeout
  static const Duration timeout = Duration(seconds: 10);
}

class AppConstants {
  static const String appName = 'BetML Pro';
  static const String appVersion = '1.0.0';
  
  // Umbral mínimo para mostrar mercado recomendado
  static const double umbralMercado = 0.60;
}

