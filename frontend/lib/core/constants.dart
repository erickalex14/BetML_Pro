class ApiConstants {
  // Se fija en tiempo de BUILD, no en runtime:
  //   flutter build apk --dart-define=API_BASE_URL=http://IP:PUERTO
  // Sin el flag queda en localhost, que sirve para desarrollo web pero
  // NO para un APK (en un celular "localhost" es el propio celular).
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://novitec.com.ec/betml',
  );

  static const String partidosHoy = '/partidos/hoy';
  static const String partido = '/partidos';
  static const String prediccionesHoy = '/predicciones/hoy';
  static const String prediccionesMias = '/predicciones/mias';
  static const String recomendadas = '/predicciones/recomendadas';
  static const String statsModelo = '/stats/modelo';

  static const String authLogin = '/auth/login';
  static const String authRegistro = '/auth/registro';
  static const String authMe = '/auth/me';
  static const String authGoogle = '/auth/google';
  static const String authRefresh = '/auth/refresh';
  static const String authLogout = '/auth/logout';
  static const String googleClientId = String.fromEnvironment(
    'GOOGLE_CLIENT_ID',
    defaultValue:
        '375958698814-c7aufka09t7669o4ujg74cc0svu7dn1m.apps.googleusercontent.com',
  );

  static String kelly(int partidoId) => '/predicciones/$partidoId/kelly';
  static String guardarMercados(int partidoId) =>
      '/predicciones/$partidoId/guardar-mercados';
  static String kellyPortafolio(int partidoId) =>
      '/predicciones/$partidoId/kelly/portafolio';
  static String jugadores(int partidoId) =>
      '/predicciones/$partidoId/jugadores';
  static const String combinada = '/predicciones/combinada';
  static const String analizarCaptura = '/predicciones/analizar-captura';

  //Timeout
  static const Duration timeout = Duration(seconds: 10);
}

class AppConstants {
  static const String appName = 'BetML Pro';
  static const String appVersion = '0.4.9';

  // Umbral mínimo para mostrar mercado recomendado
  static const double umbralMercado = 0.60;
}
