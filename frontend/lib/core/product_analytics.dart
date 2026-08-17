import 'package:flutter/foundation.dart';

/// Punto unico para eventos UX. Por ahora usa debugPrint: no envia PII ni
/// introduce un proveedor externo antes de elegirlo y documentar consentimiento.
abstract final class ProductAnalytics {
  static void track(String event, [Map<String, Object?> data = const {}]) {
    assert(() {
      debugPrint('[analytics] $event $data');
      return true;
    }());
  }
}
