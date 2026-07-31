import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme.dart';
import '../providers/stats_provider.dart';

class StatsScreen extends StatefulWidget {
  const StatsScreen({super.key});

  @override
  State<StatsScreen> createState() => _StatsScreenState();
}

class _StatsScreenState extends State<StatsScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      if (mounted) {
        context.read<StatsProvider>().cargar();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppTheme.textSecond),
          onPressed: () => context.go('/'),
        ),
        title: const Text('Stats del Modelo'),
      ),
      body: Consumer<StatsProvider>(
        builder: (ctx, provider, _) {
          if (provider.cargando) {
            return const Center(
              child: CircularProgressIndicator(color: AppTheme.primary));
          }
          if (provider.error != null) {
            return Center(
              child: Text(provider.error!,
                style: const TextStyle(color: AppTheme.red)));
          }
          if (provider.stats == null) {
            return const Center(
              child: Text('Sin datos',
                style: TextStyle(color: AppTheme.textSecond)));
          }
          final s = provider.stats!;
          return Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('RENDIMIENTO DEL MODELO',
                  style: TextStyle(
                    color: AppTheme.textSecond,
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 1)),
                const SizedBox(height: 12),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      children: [
                        _StatBox('Precisión', s.accuracyStr, AppTheme.primary),
                        _StatBox('Acertadas', '${s.acertadas}', AppTheme.primary),
                        _StatBox('Falladas', '${s.falladas}', AppTheme.red),
                        _StatBox('Pendientes', '${s.pendientes}', AppTheme.amber),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Total predicciones',
                          style: TextStyle(color: AppTheme.textSecond)),
                        Text('${s.total}',
                          style: const TextStyle(
                            fontWeight: FontWeight.w600)),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _StatBox extends StatelessWidget {
  final String label, valor;
  final Color  color;
  const _StatBox(this.label, this.valor, this.color);

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      Text(valor,
        style: TextStyle(
          color: color,
          fontSize: 24,
          fontWeight: FontWeight.w700)),
      const SizedBox(height: 4),
      Text(label,
        style: const TextStyle(
          color: AppTheme.textSecond, fontSize: 11)),
    ]);
  }
}