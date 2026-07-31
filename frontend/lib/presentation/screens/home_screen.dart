import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme.dart';
import '../providers/partidos_provider.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      if (mounted) context.read<PartidosProvider>().cargarPartidosHoy();
      }
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: Row(children: [
          Container(
            width: 28, height: 28,
            decoration: BoxDecoration(
              color: AppTheme.primary,
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(Icons.sports_soccer,
              color: Colors.white, size: 16),
          ),
          const SizedBox(width: 10),
          const Text('BetML Pro'),
        ]),
        actions: [
          IconButton(
            icon: const Icon(Icons.bar_chart, color: AppTheme.textSecond),
            onPressed: () => context.go('/stats'),
          ),
          IconButton(
            icon: const Icon(Icons.refresh, color: AppTheme.textSecond),
            onPressed: () =>
              context.read<PartidosProvider>().cargarPartidosHoy(),
          ),
        ],
      ),
      body: Consumer<PartidosProvider>(
        builder: (context, provider, _) {
          if (provider.cargando) {
            return const Center(
              child: CircularProgressIndicator(color: AppTheme.primary));
          }
          if (provider.error != null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline,
                    color: AppTheme.red, size: 48),
                  const SizedBox(height: 12),
                  Text(provider.error!,
                    style: const TextStyle(color: AppTheme.textSecond),
                    textAlign: TextAlign.center),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: provider.cargarPartidosHoy,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.primary),
                    child: const Text('Reintentar'),
                  ),
                ],
              ),
            );
          }
          if (provider.partidos.isEmpty) {
            return const Center(
              child: Text('No hay partidos hoy',
                style: TextStyle(color: AppTheme.textSecond)));
          }
          return Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('${provider.partidos.length} partidos hoy',
                      style: const TextStyle(
                        color: AppTheme.textSecond, fontSize: 13)),
                    Text(provider.fecha,
                      style: const TextStyle(
                        color: AppTheme.textSecond, fontSize: 13)),
                  ],
                ),
              ),
              // Filtro ligas
              _LigaFilter(provider: provider),
              const SizedBox(height: 8),
              Expanded(
                child: ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  itemCount: provider.porLiga.length,
                  itemBuilder: (context, i) {
                    final p = provider.porLiga[i];
                    return _PartidoCard(
                      partido: p,
                      onTap: () => context.go('/partido/${p.id}'),
                    );
                  },
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _LigaFilter extends StatelessWidget {
  final PartidosProvider provider;
  const _LigaFilter({required this.provider});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 36,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        children: [
          _Chip(label: 'Todos',
            selected: provider.ligaFiltro == null,
            onTap: () => provider.setFiltroLiga(null)),
          ...provider.ligasDisponibles.map((liga) => _Chip(
            label: liga,
            selected: provider.ligaFiltro == liga,
            onTap: () => provider.setFiltroLiga(liga),
          )),
        ],
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;
  const _Chip({required this.label, required this.selected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(right: 6),
        padding: const EdgeInsets.symmetric(horizontal: 12),
        decoration: BoxDecoration(
          color: selected ? AppTheme.primary : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: selected ? AppTheme.primary : AppTheme.border,
            width: 0.5),
        ),
        child: Center(
          child: Text(label,
            style: TextStyle(
              color: selected ? Colors.white : AppTheme.textSecond,
              fontSize: 12)),
        ),
      ),
    );
  }
}

class _PartidoCard extends StatelessWidget {
  final dynamic partido;
  final VoidCallback onTap;
  const _PartidoCard({required this.partido, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(children: [
                    Container(
                      width: 6, height: 6,
                      decoration: const BoxDecoration(
                        color: AppTheme.primary,
                        shape: BoxShape.circle),
                    ),
                    const SizedBox(width: 6),
                    Text(partido.liga,
                      style: const TextStyle(
                        color: AppTheme.textSecond, fontSize: 11)),
                  ]),
                  Text(partido.hora,
                    style: const TextStyle(
                      color: AppTheme.textSecond, fontSize: 11)),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: Text(partido.local,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 14, fontWeight: FontWeight.w500)),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppTheme.surface2,
                      borderRadius: BorderRadius.circular(6)),
                    child: Text(partido.marcador,
                      style: TextStyle(
                        color: partido.terminado
                          ? AppTheme.textPrimary
                          : AppTheme.textSecond,
                        fontSize: 13,
                        fontWeight: FontWeight.w600)),
                  ),
                  Expanded(
                    child: Text(partido.visitante,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 14, fontWeight: FontWeight.w500)),
                  ),
                ],
              ),
              if (partido.tienePred) ...[
                const SizedBox(height: 10),
                const Divider(color: AppTheme.border, height: 1),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                        children: [
                          _ProbBox('L', partido.prediccion!.probLocal,
                            partido.prediccion!.resultado == 'Local'),
                          _ProbBox('E', partido.prediccion!.probEmpate,
                            partido.prediccion!.resultado == 'Empate'),
                          _ProbBox('V', partido.prediccion!.probVisitante,
                            partido.prediccion!.resultado == 'Visitante'),
                        ],
                      ),
                    ),
                    if (partido.prediccion!.mercadosTop.isNotEmpty)
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: AppTheme.amber.withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                            color: AppTheme.amber, width: 0.5)),
                        child: Text(
                          partido.prediccion!.mercadosTop.first.label,
                          style: const TextStyle(
                            color: AppTheme.amber,
                            fontSize: 11,
                            fontWeight: FontWeight.w500)),
                      ),
                  ],
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _ProbBox extends StatelessWidget {
  final String label;
  final double prob;
  final bool   highlight;
  const _ProbBox(this.label, this.prob, this.highlight);

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      Text(label,
        style: TextStyle(
          color: highlight ? AppTheme.primary : AppTheme.textSecond,
          fontSize: 10, fontWeight: FontWeight.w500)),
      const SizedBox(height: 2),
      Text('${(prob * 100).toStringAsFixed(0)}%',
        style: TextStyle(
          color: highlight ? AppTheme.primary : AppTheme.textSecond,
          fontSize: 12,
          fontWeight: highlight ? FontWeight.w600 : FontWeight.normal)),
    ]);
  }
}