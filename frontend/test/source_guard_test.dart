import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('análisis avanzado se apila sobre el detalle', () {
    final source =
        File('lib/presentation/screens/detalle_screen.dart').readAsStringSync();

    expect(
      source,
      contains("context.push('/partido/\${partido.id}/avanzado')"),
    );
    expect(
      source,
      isNot(contains("context.go('/partido/\${partido.id}/avanzado')")),
    );
  });

  test('la interfaz no contiene indicadores comunes de mojibake', () {
    final dartFiles = Directory('lib')
        .listSync(recursive: true)
        .whereType<File>()
        .where((file) => file.path.endsWith('.dart'));
    final corruptos = <String>[];

    for (final file in dartFiles) {
      final source = file.readAsStringSync();
      if (source.contains('Ã') ||
          source.contains('Â') ||
          source.contains('�')) {
        corruptos.add(file.path);
      }
    }

    expect(corruptos, isEmpty,
        reason: 'Archivos con texto UTF-8 corrupto: ${corruptos.join(', ')}');
  });

  test('la interfaz usa español latino neutro', () {
    final dartFiles = Directory('lib/presentation')
        .listSync(recursive: true)
        .whereType<File>()
        .where((file) => file.path.endsWith('.dart'));
    final voseo = RegExp(
        r'\b(tenés|necesitás|elegí|ingresá|usá|tocá|guardá|revisá|volvé|combiná|medí)\b',
        caseSensitive: false);
    final encontrados = <String>[];

    for (final file in dartFiles) {
      if (voseo.hasMatch(file.readAsStringSync())) {
        encontrados.add(file.path);
      }
    }

    expect(encontrados, isEmpty,
        reason: 'Pantallas con voseo: ${encontrados.join(', ')}');
  });

  test('el APK sin dart-define conserva configuracion de produccion segura',
      () {
    final source = File('lib/core/constants.dart').readAsStringSync();

    expect(source, contains("defaultValue: 'https://novitec.com.ec/betml'"));
    expect(source, contains('375958698814-c7aufka09t7669o4ujg74cc0svu7dn1m'));
    expect(source, isNot(contains("defaultValue: 'http://localhost:8001'")));
  });
}
