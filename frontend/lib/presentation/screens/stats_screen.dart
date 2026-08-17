import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme.dart';
import '../../core/product_analytics.dart';
import '../providers/stats_provider.dart';
import '../widgets/app_bottom_nav.dart';
import '../widgets/clay.dart';
import '../widgets/design_system.dart';

class StatsScreen extends StatefulWidget {
  const StatsScreen({super.key});

  @override
  State<StatsScreen> createState() => _StatsScreenState();
}

class _StatsScreenState extends State<StatsScreen> {
  @override
  void initState() {
    super.initState();
    ProductAnalytics.track('screen_view', {'screen': 'rendimiento'});
    Future.microtask(() {
      if (mounted) context.read<StatsProvider>().cargar();
    });
  }

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Scaffold(
      appBar: const AppHeader(
          title: 'Rendimiento',
          subtitle: 'Modelo y actividad personal, sin mezclar'),
      body: Consumer<StatsProvider>(
        builder: (ctx, provider, _) {
          if (provider.cargando) {
            return Center(child: CircularProgressIndicator(color: c.pitch));
          }
          if (provider.error != null) {
            return Center(
                child: Text(provider.error!, style: TextStyle(color: c.brick)));
          }
          if (provider.stats == null) {
            return Center(
                child:
                    Text('Sin datos', style: TextStyle(color: c.textSecond)));
          }
          final s = provider.stats!;
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              const SectionHeading('Modelo',
                  subtitle: 'Resultados de todas las predicciones cerradas'),
              const SizedBox(height: 12),
              ClayContainer(
                padding: const EdgeInsets.all(18),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    _StatBox('Precisión', s.accuracyStr, c.pitch, c),
                    _StatBox('Acertadas', '${s.acertadas}', c.pitch, c),
                    _StatBox('Falladas', '${s.falladas}', c.brick, c),
                    _StatBox('Pendientes', '${s.pendientes}', c.ledger, c),
                  ],
                ),
              ),
              const SizedBox(height: 12),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Total predicciones',
                          style: TextStyle(color: c.textSecond)),
                      Text('${s.total}', style: AppTheme.score(c, size: 15)),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              const SectionHeading('Tu actividad',
                  subtitle: 'Solo selecciones guardadas en tu portafolio'),
              const SizedBox(height: 12),
              Card(
                  child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                          'El rendimiento personal se calcula desde tus selecciones cerradas.',
                          style: TextStyle(color: c.textSecond, height: 1.4)),
                      const SizedBox(height: 12),
                      OutlinedButton.icon(
                        onPressed: () => context.go('/portafolio'),
                        icon: const Icon(Icons.bookmark_outline_rounded),
                        label: const Text('Abrir portafolio'),
                      ),
                    ]),
              )),
            ],
          );
        },
      ),
      bottomNavigationBar: const AppBottomNav(current: AppTab.rendimiento),
    );
  }
}

class _StatBox extends StatelessWidget {
  final String label, valor;
  final Color color;
  final AppColors c;
  const _StatBox(this.label, this.valor, this.color, this.c);

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      Text(valor, style: AppTheme.score(c, size: 22).copyWith(color: color)),
      const SizedBox(height: 4),
      Text(label, style: TextStyle(color: c.textSecond, fontSize: 11)),
    ]);
  }
}
