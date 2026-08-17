import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/domain/entities/parlay.dart';
import 'package:frontend/presentation/providers/prediction_coupon_provider.dart';
import 'package:frontend/presentation/widgets/app_bottom_nav.dart';
import 'package:provider/provider.dart';

CouponSelection selection(int partidoId, String mercado) => CouponSelection(
      input: ParlaySeleccionInput(
          partidoId: partidoId, mercado: mercado, cuota: 1.8),
      partido: 'Local vs Visitante',
      liga: 'Liga',
      mercado: mercado,
      probabilidad: .65,
    );

void main() {
  test('agrega, reemplaza y quita una selección por partido', () {
    final coupon = PredictionCouponProvider();

    coupon.toggle(selection(1, 'local'));
    expect(coupon.count, 1);

    coupon.toggle(selection(1, 'over_2_5'));
    expect(coupon.count, 1);
    expect(coupon.items.single.input.mercado, 'over_2_5');

    coupon.toggle(selection(1, 'over_2_5'));
    expect(coupon.isEmpty, isTrue);
  });

  testWidgets('el botón flotante abre el cupón', (tester) async {
    final coupon = PredictionCouponProvider()..toggle(selection(1, 'local'));

    await tester.pumpWidget(
      ChangeNotifierProvider.value(
        value: coupon,
        child: const MaterialApp(
          home: Scaffold(
            bottomNavigationBar: AppBottomNav(current: AppTab.hoy),
          ),
        ),
      ),
    );

    final button = find.byTooltip('Abrir cupón');
    expect(button.hitTestable(), findsOneWidget);
    await tester.tap(button);
    await tester.pumpAndSettle();

    expect(find.textContaining('Cupón de predicciones'), findsOneWidget);
  });
}
