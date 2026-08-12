import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme.dart';
import '../../core/errors/failures.dart';
import '../../domain/entities/recomendadas.dart';
import '../../domain/usecases/get_recomendadas.dart';
import '../../data/repositories/partido_repo_impl.dart';
import '../widgets/app_bottom_nav.dart';
import '../widgets/clay.dart';

class RecomendadasScreen extends StatefulWidget {
  const RecomendadasScreen({super.key});

  @override
  State<RecomendadasScreen> createState() => _RecomendadasScreenState();
}

class _RecomendadasScreenState extends State<RecomendadasScreen> {
  late final GetRecomendadas _getRecomendadas;
  Recomendadas? _datos;
  bool _cargando = true;
  Failure? _error;

  @override
  void initState() {
    super.initState();
    _getRecomendadas = GetRecomendadas(PartidoRepositoryImpl.create());
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() => _cargando = true);
    final r = await _getRecomendadas();
    setState(() {
      _datos = r.recomendadas;
      _error = r.error;
      _cargando = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Recomendadas', style: TextStyle(fontSize: 15)),
          actions: [IconButton(icon: Icon(Icons.refresh, color: c.textSecond), onPressed: _cargar)],
          bottom: _cargando || _error != null
              ? null
              : TabBar(
                  isScrollable: true,
                  indicatorColor: c.pitch,
                  labelColor: c.pitch,
                  unselectedLabelColor: c.textSecond,
                  tabs: [
                    Tab(text: 'INDIVIDUALES (${_datos?.apuestasIndividuales.length ?? 0})'),
                    Tab(text: 'MISMO PARTIDO (${_datos?.combinadasMismoPartido.length ?? 0})'),
                    Tab(text: 'PARLAYS (${_datos?.parlaysSugeridos.length ?? 0})'),
                  ],
                ),
        ),
        body: _cargando
            ? Center(child: CircularProgressIndicator(color: c.pitch))
            : _error != null
                ? _MensajeError(mensaje: _error!.mensaje, onRetry: _cargar)
                : _datos!.vacio
                    ? Center(
                        child: Padding(
                          padding: const EdgeInsets.all(24),
                          child: Text(
                              'Sin recomendaciones para hoy — falta historial o cuotas guardadas en los partidos del día.',
                              style: TextStyle(color: c.textSecond), textAlign: TextAlign.center),
                        ),
                      )
                    : TabBarView(children: [
                        _IndividualesTab(items: _datos!.apuestasIndividuales),
                        _CombinadasTab(items: _datos!.combinadasMismoPartido),
                        _ParlaysTab(items: _datos!.parlaysSugeridos),
                      ]),
        bottomNavigationBar: const AppBottomNav(current: AppTab.recomendadas),
      ),
    );
  }
}

class _IndividualesTab extends StatelessWidget {
  final List<ApuestaIndividual> items;
  const _IndividualesTab({required this.items});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    if (items.isEmpty) {
      return Center(child: Text('Sin value bets hoy', style: TextStyle(color: c.textSecond)));
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: items.length,
      itemBuilder: (_, i) {
        final a = items[i];
        return InkWell(
          onTap: () => context.go('/partido/${a.partidoId}'),
          borderRadius: BorderRadius.circular(13),
          child: Container(
            margin: const EdgeInsets.only(bottom: 10),
            padding: const EdgeInsets.all(13),
            decoration: BoxDecoration(
              color: c.pitchSoft,
              borderRadius: BorderRadius.circular(13),
              border: Border.all(color: c.pitch),
            ),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                Expanded(
                  child: Text('${a.local} vs ${a.visitante}',
                      style: TextStyle(fontSize: 12, color: c.textSecond)),
                ),
                Text(a.liga, style: TextStyle(fontSize: 10.5, color: c.textMuted)),
              ]),
              const SizedBox(height: 4),
              Row(children: [
                Expanded(
                  child: Text(a.mercado, style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: c.text)),
                ),
                Text('${a.stakePct.toStringAsFixed(1)}%', style: AppTheme.score(c, size: 16).copyWith(color: c.pitch)),
              ]),
              const SizedBox(height: 6),
              Text(a.porQue, style: TextStyle(fontSize: 11.5, color: c.textSecond, height: 1.35)),
            ]),
          ),
        );
      },
    );
  }
}

class _CombinadasTab extends StatelessWidget {
  final List<CombinadaMismoPartido> items;
  const _CombinadasTab({required this.items});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    if (items.isEmpty) {
      return Center(child: Text('Sin combinadas de un mismo partido con valor hoy', style: TextStyle(color: c.textSecond)));
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: items.length,
      itemBuilder: (_, i) {
        final comb = items[i];
        return InkWell(
          onTap: () => context.go('/partido/${comb.partidoId}/avanzado'),
          borderRadius: BorderRadius.circular(14),
          child: ClayContainer(
            padding: const EdgeInsets.all(15),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                Expanded(
                  child: Text('${comb.local} vs ${comb.visitante}',
                      style: TextStyle(fontSize: 13.5, fontWeight: FontWeight.w600, color: c.text)),
                ),
                Text(comb.liga, style: TextStyle(fontSize: 10.5, color: c.textMuted)),
              ]),
              const SizedBox(height: 10),
              for (final m in comb.mercados)
                Padding(
                  padding: const EdgeInsets.only(bottom: 5),
                  child: Row(children: [
                    Expanded(child: Text(m.nombre, style: TextStyle(fontSize: 12, color: c.textSecond))),
                    Text('${m.stakePct.toStringAsFixed(1)}%',
                        style: AppTheme.score(c, size: 12).copyWith(color: c.pitch)),
                  ]),
                ),
              const SizedBox(height: 6),
              Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                Text('Stake total: ${comb.stakeTotalPct.toStringAsFixed(1)}%',
                    style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.w600, color: c.text)),
                Text('EV ${(comb.evPortafolio * 100).toStringAsFixed(1)}%',
                    style: TextStyle(fontSize: 11.5, color: c.ledger)),
              ]),
            ]),
          ),
        );
      },
    );
  }
}

class _ParlaysTab extends StatelessWidget {
  final List<ParlaySugerido> items;
  const _ParlaysTab({required this.items});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    if (items.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text('Necesitás 2+ partidos con value bet hoy para armar una combinada',
              style: TextStyle(color: c.textSecond), textAlign: TextAlign.center),
        ),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: items.length,
      itemBuilder: (_, i) {
        final p = items[i];
        return Container(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: c.surface,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: c.line),
          ),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('COMBINADA DE ${p.nPatas} PATAS', style: AppTheme.eyebrow(c, color: c.ledger)),
            const SizedBox(height: 10),
            for (final pata in p.selecciones)
              Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Row(children: [
                  Container(width: 3, height: 22, decoration: BoxDecoration(color: c.pitch, borderRadius: BorderRadius.circular(2))),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text('${pata.local} vs ${pata.visitante}', style: TextStyle(fontSize: 11.5, color: c.textSecond)),
                      Text(pata.mercado, style: TextStyle(fontSize: 12.5, fontWeight: FontWeight.w600, color: c.text)),
                    ]),
                  ),
                ]),
              ),
            const Divider(height: 18),
            Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
              _dato(c, 'Cuota', p.cuotaCombinada.toStringAsFixed(2)),
              _dato(c, 'Prob', '${(p.probCombinada * 100).toStringAsFixed(1)}%'),
              _dato(c, 'Stake', '${p.stakePct.toStringAsFixed(1)}%', destacar: true),
              _dato(c, 'EV', '${(p.ev * 100).toStringAsFixed(0)}%', destacar: true),
            ]),
          ]),
        );
      },
    );
  }

  Widget _dato(AppColors c, String label, String valor, {bool destacar = false}) {
    return Column(children: [
      Text(valor, style: AppTheme.score(c, size: 14).copyWith(color: destacar ? c.pitch : c.text)),
      const SizedBox(height: 2),
      Text(label, style: TextStyle(fontSize: 10, color: c.textSecond)),
    ]);
  }
}

class _MensajeError extends StatelessWidget {
  final String mensaje;
  final VoidCallback onRetry;
  const _MensajeError({required this.mensaje, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Text(mensaje, style: TextStyle(color: c.brick), textAlign: TextAlign.center),
          const SizedBox(height: 12),
          OutlinedButton(
            onPressed: onRetry,
            style: OutlinedButton.styleFrom(foregroundColor: c.brick, side: BorderSide(color: c.brick)),
            child: const Text('Reintentar'),
          ),
        ]),
      ),
    );
  }
}
