import 'package:go_router/go_router.dart';
import '../presentation/screens/home_screen.dart';
import '../presentation/screens/detalle_screen.dart';
import '../presentation/screens/stats_screen.dart';

final appRouter = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(
      path: '/',
      builder: (ctx, state) => const HomeScreen(),
    ),
    GoRoute(
      path: '/partido/:id',
      builder: (ctx, state) => DetalleScreen(
        partidoId: int.parse(state.pathParameters['id']!),
      ),
    ),
    GoRoute(
      path: '/stats',
      builder: (ctx, state) => const StatsScreen(),
    ),
  ],
);