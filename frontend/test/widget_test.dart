import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/core/theme.dart';
import 'package:frontend/presentation/widgets/confidence.dart';
import 'package:frontend/presentation/widgets/clay.dart';
import 'package:frontend/presentation/widgets/app_bottom_nav.dart';
import 'package:frontend/presentation/widgets/design_system.dart';
import 'package:frontend/domain/entities/partido.dart';

// No pumpeamos BetMLApp completo — arranca AuthProvider, que lee
// FlutterSecureStorage, y ese plugin no tiene canal de plataforma
// mockeado en el entorno de test (cuelga con un timer pendiente).
// Estos widgets propios sí son puro Flutter, sin plugins nativos.
void main() {
  testWidgets('ConfidenceDial renderiza porcentaje y label', (tester) async {
    await tester.pumpWidget(MaterialApp(
      theme: AppTheme.darkTheme,
      home: const Scaffold(
          body: ConfidenceDial(value: 0.64, label: 'GANA LOCAL')),
    ));

    expect(find.text('64%'), findsOneWidget);
    expect(find.text('GANA LOCAL'), findsOneWidget);
  });

  testWidgets('ClayButton dispara onPressed y no dispara si loading',
      (tester) async {
    var taps = 0;
    await tester.pumpWidget(MaterialApp(
      theme: AppTheme.darkTheme,
      home: Scaffold(
          body: ClayButton(label: 'Ingresar', onPressed: () => taps++)),
    ));

    await tester.tap(find.text('Ingresar'));
    expect(taps, 1);

    await tester.pumpWidget(MaterialApp(
      theme: AppTheme.darkTheme,
      home: Scaffold(
          body: ClayButton(
              label: 'Ingresar', loading: true, onPressed: () => taps++)),
    ));
    await tester.tap(find.byType(ClayButton), warnIfMissed: false);
    expect(taps, 1); // no incrementó — loading bloquea el tap
  });

  testWidgets('navegación principal expone los cuatro destinos',
      (tester) async {
    await tester.pumpWidget(MaterialApp(
      theme: AppTheme.darkTheme,
      home: const Scaffold(
        body: SizedBox.shrink(),
        bottomNavigationBar: AppBottomNav(current: AppTab.hoy),
      ),
    ));

    expect(find.text('Hoy'), findsOneWidget);
    expect(find.text('Oportunidades'), findsOneWidget);
    expect(find.text('Portafolio'), findsOneWidget);
    expect(find.text('Rendimiento'), findsOneWidget);
    expect(find.byType(NavigationDestination), findsNWidgets(4));
  });

  testWidgets('estado vacío mantiene mensaje y objetivo táctil accesible',
      (tester) async {
    await tester.pumpWidget(MaterialApp(
      theme: AppTheme.lightTheme,
      home: const Scaffold(
        body: AppStateView(
          icon: Icons.bookmark_border,
          title: 'Portafolio vacío',
          message: 'Guardá una oportunidad para seguirla.',
          action: 'Explorar',
          onAction: _noop,
        ),
      ),
    ));

    expect(find.text('Portafolio vacío'), findsOneWidget);
    expect(
        tester.getSize(find.widgetWithText(OutlinedButton, 'Explorar')).height,
        greaterThanOrEqualTo(48));
  });

  testWidgets('Atrás en Hoy avisa antes de permitir salir', (tester) async {
    await tester.pumpWidget(MaterialApp(
      theme: AppTheme.darkTheme,
      home: const AppRootBackGuard(
        isHome: true,
        child: Scaffold(body: Text('Hoy')),
      ),
    ));

    await tester.binding.handlePopRoute();
    await tester.pump();

    expect(find.text('Deslizá nuevamente para salir'), findsOneWidget);
  });

  test('Partido conserva la hora local recibida sin reconvertir zona', () {
    final partido = Partido(
      id: 1,
      liga: 'Liga',
      ligaId: 1,
      local: 'Local',
      localId: 1,
      visitante: 'Visita',
      visitanteId: 2,
      fecha: DateTime(2026, 8, 14, 19, 30),
      estado: 'NS',
      temporada: 2026,
    );

    expect(partido.hora, '19:30');
    expect(partido.fechaHoraLarga, contains('14 ago 2026'));
  });
}

void _noop() {}
