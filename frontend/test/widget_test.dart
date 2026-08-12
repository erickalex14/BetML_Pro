import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/core/theme.dart';
import 'package:frontend/presentation/widgets/confidence.dart';
import 'package:frontend/presentation/widgets/clay.dart';

// No pumpeamos BetMLApp completo — arranca AuthProvider, que lee
// FlutterSecureStorage, y ese plugin no tiene canal de plataforma
// mockeado en el entorno de test (cuelga con un timer pendiente).
// Estos widgets propios sí son puro Flutter, sin plugins nativos.
void main() {
  testWidgets('ConfidenceDial renderiza porcentaje y label', (tester) async {
    await tester.pumpWidget(MaterialApp(
      theme: AppTheme.darkTheme,
      home: const Scaffold(body: ConfidenceDial(value: 0.64, label: 'GANA LOCAL')),
    ));

    expect(find.text('64%'), findsOneWidget);
    expect(find.text('GANA LOCAL'), findsOneWidget);
  });

  testWidgets('ClayButton dispara onPressed y no dispara si loading', (tester) async {
    var taps = 0;
    await tester.pumpWidget(MaterialApp(
      theme: AppTheme.darkTheme,
      home: Scaffold(body: ClayButton(label: 'Ingresar', onPressed: () => taps++)),
    ));

    await tester.tap(find.text('Ingresar'));
    expect(taps, 1);

    await tester.pumpWidget(MaterialApp(
      theme: AppTheme.darkTheme,
      home: Scaffold(body: ClayButton(label: 'Ingresar', loading: true, onPressed: () => taps++)),
    ));
    await tester.tap(find.byType(ClayButton), warnIfMissed: false);
    expect(taps, 1); // no incrementó — loading bloquea el tap
  });
}
