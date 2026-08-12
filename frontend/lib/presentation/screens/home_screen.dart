import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme.dart';
import '../../domain/entities/partido.dart';
import '../providers/partidos_provider.dart';
import '../widgets/clay.dart';
import '../widgets/confidence.dart';
import '../widgets/app_bottom_nav.dart';
import '../widgets/team_logo.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  Timer? _autoRefresh;

  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      if (mounted) context.read<PartidosProvider>().cargarPartidosHoy();
    });
    // el backend refresca marcador/estado cada 15 min (job_partidos_en_vivo)
    // — 60s alcanza para que se sienta "en vivo" sin bombardear al propio
    // backend con requests que igual van a devolver lo mismo la mayoría
    // de las veces
    _autoRefresh = Timer.periodic(const Duration(seconds: 60), (_) {
      if (mounted) context.read<PartidosProvider>().cargarPartidosHoy(mostrarCargando: false);
    });
  }

  @override
  void dispose() {
    _autoRefresh?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Scaffold(
      appBar: AppBar(
        title: Row(mainAxisSize: MainAxisSize.min, children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: Image.asset('assets/logos/logo_icon.png', width: 28, height: 28),
          ),
          const SizedBox(width: 10),
          const Text('Partidos'),
        ]),
        actions: [
          IconButton(
            icon: Icon(Icons.image_search_rounded, color: c.textSecond),
            tooltip: 'Analizar captura',
            onPressed: () => context.go('/analizar-captura'),
          ),
          IconButton(
            icon: Icon(Icons.dashboard_customize_outlined, color: c.textSecond),
            tooltip: 'Armar combinada',
            onPressed: () => context.go('/parlay'),
          ),
          IconButton(
            icon: Icon(Icons.refresh, color: c.textSecond),
            onPressed: () => context.read<PartidosProvider>().cargarPartidosHoy(),
          ),
        ],
      ),
      body: Consumer<PartidosProvider>(
        builder: (context, provider, _) {
          if (provider.cargando) return _CargandoLista();
          if (provider.error != null) {
            return _Error(mensaje: provider.error!, onRetry: provider.cargarPartidosHoy);
          }
          if (provider.partidos.isEmpty) {
            return _Vacio();
          }

          final destacado = provider.topPicks.isNotEmpty ? provider.topPicks.first : null;
          final resto = provider.porLiga.where((p) => p.id != destacado?.id).toList();

          return ListView(
            padding: const EdgeInsets.only(top: 8, bottom: 8),
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 10),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('${provider.partidos.length} partidos hoy',
                        style: TextStyle(color: c.textSecond, fontSize: 13)),
                    Text(provider.fecha, style: AppTheme.eyebrow(c)),
                  ],
                ),
              ),
              if (destacado != null) ...[
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: _FeaturedCard(partido: destacado),
                ),
                const SizedBox(height: 16),
              ],
              _LigaFilter(provider: provider),
              const SizedBox(height: 4),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Column(
                  children: resto.map((p) => _LedgerRow(partido: p)).toList(),
                ),
              ),
            ],
          );
        },
      ),
      bottomNavigationBar: const AppBottomNav(current: AppTab.partidos),
    );
  }
}

class _FeaturedCard extends StatelessWidget {
  final Partido partido;
  const _FeaturedCard({required this.partido});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final pred = partido.prediccion!;
    return ClayContainer(
      padding: const EdgeInsets.fromLTRB(17, 16, 17, 15),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(color: c.ledgerSoft, borderRadius: BorderRadius.circular(5)),
            child: Text('Alta confianza', style: AppTheme.eyebrow(c, color: c.ledger)),
          ),
          Text(partido.liga, style: TextStyle(color: c.textSecond, fontSize: 11.5)),
        ]),
        const SizedBox(height: 10),
        Row(children: [
          Expanded(
            child: Column(children: [
              TeamLogo(url: partido.localLogo, nombre: partido.local, size: 32),
              const SizedBox(height: 6),
              Text(partido.local, textAlign: TextAlign.center, maxLines: 2,
                  style: TextStyle(fontSize: 13.5, fontWeight: FontWeight.w600, color: c.text)),
            ]),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 10),
            child: Column(children: [
              Text(partido.hora, style: AppTheme.score(c, size: 15)),
              Text('hoy', style: TextStyle(fontSize: 10, color: c.textSecond)),
            ]),
          ),
          Expanded(
            child: Column(children: [
              TeamLogo(url: partido.visitanteLogo, nombre: partido.visitante, size: 32),
              const SizedBox(height: 6),
              Text(partido.visitante, textAlign: TextAlign.center, maxLines: 2,
                  style: TextStyle(fontSize: 13.5, fontWeight: FontWeight.w600, color: c.text)),
            ]),
          ),
        ]),
        const SizedBox(height: 12),
        Row(children: [
          _prob('LOCAL', pred.probLocal, pred.resultado == 'Local', c),
          const SizedBox(width: 8),
          _prob('EMPATE', pred.probEmpate, pred.resultado == 'Empate', c),
          const SizedBox(width: 8),
          _prob('VISITA', pred.probVisitante, pred.resultado == 'Visitante', c),
        ]),
        const SizedBox(height: 12),
        Row(children: [
          Text('Confianza', style: TextStyle(fontSize: 11, color: c.textSecond)),
          const SizedBox(width: 10),
          Expanded(child: ConfidenceMeter(value: pred.confianza)),
        ]),
        const SizedBox(height: 13),
        ClayButton(label: 'Ver análisis completo', onPressed: () => context.go('/partido/${partido.id}')),
      ]),
    );
  }

  Widget _prob(String label, double prob, bool hi, AppColors c) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 9),
        decoration: BoxDecoration(color: hi ? c.pitch : c.bg2, borderRadius: BorderRadius.circular(12)),
        child: Column(children: [
          Text('${(prob * 100).toStringAsFixed(0)}%',
              style: AppTheme.score(c, size: 16).copyWith(color: hi ? c.bg : c.text)),
          const SizedBox(height: 1),
          Text(label, style: TextStyle(fontSize: 9.5, color: hi ? c.bg.withValues(alpha: 0.75) : c.textSecond)),
        ]),
      ),
    );
  }
}

class _LigaFilter extends StatelessWidget {
  final PartidosProvider provider;
  const _LigaFilter({required this.provider});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return SizedBox(
      height: 34,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        children: [
          _Chip(label: 'Todos', selected: provider.ligaFiltro == null, onTap: () => provider.setFiltroLiga(null), c: c),
          ...provider.ligasDisponibles.map((liga) => _Chip(
                label: liga, selected: provider.ligaFiltro == liga, onTap: () => provider.setFiltroLiga(liga), c: c,
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
  final AppColors c;
  const _Chip({required this.label, required this.selected, required this.onTap, required this.c});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(right: 6),
        padding: const EdgeInsets.symmetric(horizontal: 13),
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: selected ? c.pitch : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: selected ? c.pitch : c.lineStrong, width: 0.7),
        ),
        child: Text(label, style: TextStyle(color: selected ? c.bg : c.textSecond, fontSize: 12, fontWeight: selected ? FontWeight.w600 : FontWeight.normal)),
      ),
    );
  }
}

// Fila ledger — regla horizontal, no card repetida. La barra lateral
// marca si el pick es fuerte (pitch) o no hay predicción (línea).
class _LedgerRow extends StatelessWidget {
  final Partido partido;
  const _LedgerRow({required this.partido});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final pred = partido.prediccion;
    final fuerte = pred != null && pred.altaConfianza;

    return InkWell(
      onTap: () => context.go('/partido/${partido.id}'),
      child: Container(
        decoration: BoxDecoration(border: Border(bottom: BorderSide(color: c.line))),
        padding: const EdgeInsets.symmetric(vertical: 11),
        child: Row(children: [
          Container(width: 3, height: 30, decoration: BoxDecoration(
              color: fuerte ? c.pitch : c.lineStrong, borderRadius: BorderRadius.circular(2))),
          const SizedBox(width: 11),
          SizedBox(
            width: 44,
            child: Stack(children: [
              TeamLogo(url: partido.localLogo, nombre: partido.local, size: 22),
              Positioned(
                left: 14,
                child: Container(
                  padding: const EdgeInsets.all(1.5),
                  decoration: BoxDecoration(color: c.bg, shape: BoxShape.circle),
                  child: TeamLogo(url: partido.visitanteLogo, nombre: partido.visitante, size: 22),
                ),
              ),
            ]),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(partido.liga.toUpperCase(), style: AppTheme.eyebrow(c)),
              const SizedBox(height: 3),
              Text('${partido.local} — ${partido.visitante}',
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(fontSize: 13.5, fontWeight: FontWeight.w500, color: c.text)),
            ]),
          ),
          const SizedBox(width: 8),
          Text(partido.marcador, style: AppTheme.score(c, size: 12, weight: FontWeight.w500).copyWith(color: c.textSecond)),
          const SizedBox(width: 10),
          Container(
            width: 32, height: 32,
            decoration: BoxDecoration(
              color: fuerte ? c.pitchSoft : c.bg2,
              borderRadius: BorderRadius.circular(9),
            ),
            alignment: Alignment.center,
            child: Text(
              pred != null ? pred.resultado[0] : '-',
              style: AppTheme.score(c, size: 12).copyWith(color: fuerte ? c.pitch : c.textSecond),
            ),
          ),
        ]),
      ),
    );
  }
}

class _CargandoLista extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: 6,
      itemBuilder: (_, __) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 10),
        child: Row(children: [
          _Shimmer(c, width: 34, height: 34, radius: 10),
          const SizedBox(width: 12),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            _Shimmer(c, width: 120, height: 10),
            const SizedBox(height: 8),
            _Shimmer(c, width: 70, height: 10),
          ])),
        ]),
      ),
    );
  }
}

class _Shimmer extends StatelessWidget {
  final AppColors c;
  final double width, height;
  final double radius;
  const _Shimmer(this.c, {required this.width, required this.height, this.radius = 4});

  @override
  Widget build(BuildContext context) {
    return Container(width: width, height: height,
        decoration: BoxDecoration(color: c.bg2, borderRadius: BorderRadius.circular(radius)));
  }
}

class _Vacio extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Icon(Icons.event_busy_outlined, size: 40, color: c.textMuted),
          const SizedBox(height: 14),
          Text('Sin partidos hoy', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: c.text)),
          const SizedBox(height: 5),
          Text('El scheduler corre a las 23:55.\nVolvé a revisar más tarde.',
              textAlign: TextAlign.center, style: TextStyle(fontSize: 12.5, color: c.textSecond)),
        ]),
      ),
    );
  }
}

class _Error extends StatelessWidget {
  final String mensaje;
  final VoidCallback onRetry;
  const _Error({required this.mensaje, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(color: c.brickSoft, borderRadius: BorderRadius.circular(12)),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Icon(Icons.error_outline_rounded, color: c.brick, size: 22),
            const SizedBox(height: 8),
            Text('No pudimos conectar', style: TextStyle(fontWeight: FontWeight.w600, color: c.brick, fontSize: 13)),
            const SizedBox(height: 4),
            Text(mensaje, textAlign: TextAlign.center, style: TextStyle(fontSize: 12, color: c.textSecond)),
            const SizedBox(height: 12),
            OutlinedButton(
              onPressed: onRetry,
              style: OutlinedButton.styleFrom(foregroundColor: c.brick, side: BorderSide(color: c.brick)),
              child: const Text('Reintentar'),
            ),
          ]),
        ),
      ),
    );
  }
}
