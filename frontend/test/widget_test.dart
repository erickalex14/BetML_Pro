import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/main.dart';

void main() {
  testWidgets('BetML Pro smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const BetMLApp());
    expect(find.text('BetML Pro'), findsOneWidget);
  });
}