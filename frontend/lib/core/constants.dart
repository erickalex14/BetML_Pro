class ApiConstants {
  static const String baseUrl = 'http://localhost:8001';

  static const String partidosHoy = '/partidos/hoy';
  static const String partido = '/partidos';
  static const String prediccionesHoy= '/predicciones/hoy';
  static const String prediccionesMias = '/predicciones/mias';
  static const String recomendadas = '/predicciones/recomendadas';
  static const String statsModelo    = '/stats/modelo';

  static const String authLogin   = '/auth/login';
  static const String authRegistro = '/auth/registro';
  static const String authMe = '/auth/me';

  static String kelly(int partidoId) => '/predicciones/$partidoId/kelly';
  static String guardarMercados(int partidoId) => '/predicciones/$partidoId/guardar-mercados';
  static String kellyPortafolio(int partidoId) => '/predicciones/$partidoId/kelly/portafolio';
  static String jugadores(int partidoId) => '/predicciones/$partidoId/jugadores';
  static const String combinada = '/predicciones/combinada';
  static const String analizarCaptura = '/predicciones/analizar-captura';

  //Timeout
  static const Duration timeout = Duration(seconds: 10);
}

class AppConstants {
  static const String appName = 'BetML Pro';
  static const String appVersion = '1.0.0';
  
  // Umbral mínimo para mostrar mercado recomendado
  static const double umbralMercado = 0.60;
}

