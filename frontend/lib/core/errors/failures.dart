sealed class Failure {
  final String mensaje;
  const Failure(this.mensaje);
}

//Error de conexion a la API
class NetworkFailure extends Failure {
  const NetworkFailure(super.mensaje);
}

// La API respondió pero con error (404, 500, etc)
class ServerFailure extends Failure {
  final int statusCode;
  const ServerFailure(super.mensaje, this.statusCode);
}

// No hay datos disponibles
class NotFoundFailure extends Failure {
  const NotFoundFailure(super.mensaje);
}

// Error al parsear JSON
class ParseFailure extends Failure {
  const ParseFailure(super.mensaje);
}