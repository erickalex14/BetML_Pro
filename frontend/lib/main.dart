import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'core/theme.dart';
import 'core/router.dart';
import 'presentation/providers/auth_provider.dart';
import 'presentation/providers/partidos_provider.dart';
import 'presentation/providers/stats_provider.dart';

void main() {
  runApp(const BetMLApp());
}

class BetMLApp extends StatefulWidget {
  const BetMLApp({super.key});

  @override
  State<BetMLApp> createState() => _BetMLAppState();
}

class _BetMLAppState extends State<BetMLApp> {
  // Una sola instancia — GoRouter ya re-evalúa redirect() solo via
  // refreshListenable cuando AuthProvider notifica, no hace falta (ni
  // conviene, pierde el stack de navegación) reconstruirlo en cada build.
  final _auth = AuthProvider();
  late final _router = buildRouter(_auth);

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider.value(value: _auth),
        ChangeNotifierProvider(create: (_) => PartidosProvider()),
        ChangeNotifierProvider(create: (_) => StatsProvider()),
      ],
      child: MaterialApp.router(
        title: 'BetML Pro',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.lightTheme,
        darkTheme: AppTheme.darkTheme,
        themeMode: ThemeMode.system,
        routerConfig: _router,
      ),
    );
  }
}
