import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'core/theme.dart';
import 'core/router.dart';
import 'presentation/providers/partidos_provider.dart';
import 'presentation/providers/stats_provider.dart';

void main() {
  runApp(const BetMLApp());
}

class BetMLApp extends StatelessWidget {
  const BetMLApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => PartidosProvider()),
        ChangeNotifierProvider(create: (_) => StatsProvider()),
      ],
      child: MaterialApp.router(
        title: 'BetML Pro',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.darkTheme,
        routerConfig: appRouter,
      ),
    );
  }
}
