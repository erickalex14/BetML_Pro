import 'package:go_router/go_router.dart';
import '../presentation/screens/home_screen.dart';
import '../presentation/screens/detalle_screen.dart';
import '../presentation/screens/stats_screen.dart';
import '../presentation/screens/login_screen.dart';
import '../presentation/screens/analisis_avanzado_screen.dart';
import '../presentation/screens/perfil_screen.dart';
import '../presentation/screens/mis_predicciones_screen.dart';
import '../presentation/screens/recomendadas_screen.dart';
import '../presentation/screens/parlay_screen.dart';
import '../presentation/screens/analizar_captura_screen.dart';
import '../presentation/providers/auth_provider.dart';
import '../presentation/widgets/design_system.dart';

GoRouter buildRouter(AuthProvider auth) => GoRouter(
      initialLocation: '/',
      refreshListenable: auth,
      redirect: (context, state) {
        if (auth.cargando) return null; // todavía leyendo el storage
        final vaAlLogin = state.matchedLocation == '/login';
        if (!auth.autenticado && !vaAlLogin) return '/login';
        if (auth.autenticado && vaAlLogin) return '/';
        return null;
      },
      routes: [
        GoRoute(
          path: '/login',
          builder: (ctx, state) => const LoginScreen(),
        ),
        GoRoute(
          path: '/',
          builder: (ctx, state) => const AppRootBackGuard(
            isHome: true,
            child: HomeScreen(),
          ),
        ),
        GoRoute(
          path: '/partido/:id',
          builder: (ctx, state) => AppSecondaryBackGuard(
            child: DetalleScreen(
              partidoId: int.parse(state.pathParameters['id']!),
            ),
          ),
        ),
        GoRoute(
          path: '/partido/:id/avanzado',
          builder: (ctx, state) => AnalisisAvanzadoScreen(
            partidoId: int.parse(state.pathParameters['id']!),
          ),
        ),
        GoRoute(
          path: '/stats',
          builder: (ctx, state) => const StatsScreen(),
        ),
        GoRoute(
          path: '/perfil',
          builder: (ctx, state) => const AppSecondaryBackGuard(
            child: PerfilScreen(),
          ),
        ),
        GoRoute(
          path: '/predicciones',
          builder: (ctx, state) => const MisPrediccionesScreen(),
        ),
        GoRoute(
          path: '/recomendadas',
          builder: (ctx, state) => const RecomendadasScreen(),
        ),
        GoRoute(
          path: '/oportunidades',
          builder: (ctx, state) => const AppRootBackGuard(
            isHome: false,
            child: RecomendadasScreen(),
          ),
        ),
        GoRoute(
          path: '/portafolio',
          builder: (ctx, state) => const AppRootBackGuard(
            isHome: false,
            child: MisPrediccionesScreen(),
          ),
        ),
        GoRoute(
          path: '/rendimiento',
          builder: (ctx, state) => const AppRootBackGuard(
            isHome: false,
            child: StatsScreen(),
          ),
        ),
        GoRoute(
          path: '/parlay',
          builder: (ctx, state) => const AppSecondaryBackGuard(
            fallbackRoute: '/portafolio',
            child: ParlayScreen(),
          ),
        ),
        GoRoute(
          path: '/analizar-captura',
          builder: (ctx, state) => const AppSecondaryBackGuard(
            child: AnalizarCapturaScreen(),
          ),
        ),
      ],
    );
