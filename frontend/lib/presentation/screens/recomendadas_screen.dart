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
                    Tab(text: 'INDIVIDUALES (${(_datos?.individualesFijas.length ?? 0) + (_datos?.individualesSonadoras.length ?? 0)})'),
                    Tab(text: 'MISMO PARTIDO (${(_datos?.combinadasFijas.length ?? 0) + (_datos?.combinadasSonadoras.length ?? 0)})'),
                    Tab(text: 'PARLAYS (${(_datos?.parlaysFijas.length ?? 0) + (_datos?.parlaysSonadoras.length ?? 0)})'),
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
                        _IndividualesTab(fijas: _datos!.individualesFijas, sonadoras: _datos!.individualesSonadoras),
                        _CombinadasTab(fijas: _datos!.combinadasFijas, sonadoras: _datos!.combinadasSonadoras),
                        _ParlaysTab(fijas: _datos!.parlaysFijas, sonadoras: _datos!.parlaysSonadoras),
                      ]),
        bottomNavigationBar: const AppBottomNav(current: AppTab.recomendadas),
      ),
    );
  }
}

// Header de grupo — mismo patrón en las 3 tabs, "FIJA"/"SOÑADORA" es el
// vocabulario que pidió el usuario, no una traducción de "low/high risk".
class _GrupoHeader extends StatelessWidget {
  final String titulo;
  final String subtitulo;
  final IconData icono;
  final Color color;
  const _GrupoHeader({required this.titulo, required this.subtitulo, required this.icono, required this.color});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Padding(
      padding: const EdgeInsets.fromLTRB(2, 4, 2, 10),
      child: Row(children: [
        Icon(icono, size: 15, color: color),
        const SizedBox(width: 6),
        Text(titulo, style: TextStyle(fontSize: 12.5, fontWeight: FontWeight.w700, color: color, letterSpacing: 0.3)),
        const SizedBox(width: 6),
        Expanded(child: Text(subtitulo, style: TextStyle(fontSize: 10.5, color: c.textMuted))),
      ]),
    );
  }
}

class _SinOpciones extends StatelessWidget {
  final String mensaje;
  const _SinOpciones({required this.mensaje});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Padding(
      padding: const EdgeInsets.only(bottom: 18),
      child: Text(mensaje, style: TextStyle(fontSize: 12, color: c.textMuted)),
    );
  }
}

class _IndividualesTab extends StatelessWidget {
  final List<ApuestaIndividual> fijas;
  final List<ApuestaIndividual> sonadoras;
  const _IndividualesTab({required this.fijas, required this.sonadoras});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    if (fijas.isEmpty && sonadoras.isEmpty) {
      return Center(child: Text('Sin value bets hoy', style: TextStyle(color: c.textSecond)));
    }
    Widget tarjeta(ApuestaIndividual a, Color acento) => InkWell(
          onTap: () => context.go('/partido/${a.partidoId}'),
          borderRadius: BorderRadius.circular(13),
          child: Container(
            margin: const EdgeInsets.only(bottom: 10),
            padding: const EdgeInsets.all(13),
            decoration: BoxDecoration(
              color: c.pitchSoft,
              borderRadius: BorderRadius.circular(13),
              border: Border.all(color: acento),
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
                Text('${a.cuota.toStringAsFixed(2)} · ${a.stakePct.toStringAsFixed(1)}%',
                    style: AppTheme.score(c, size: 15).copyWith(color: acento)),
              ]),
              const SizedBox(height: 6),
              Text(a.porQue, style: TextStyle(fontSize: 11.5, color: c.textSecond, height: 1.35)),
            ]),
          ),
        );
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _GrupoHeader(titulo: 'FIJAS', subtitulo: 'alta probabilidad, poco riesgo', icono: Icons.shield_rounded, color: c.pitch),
        if (fijas.isEmpty) const _SinOpciones(mensaje: 'Nada suficientemente seguro hoy.') else ...fijas.map((a) => tarjeta(a, c.pitch)),
        const SizedBox(height: 8),
        _GrupoHeader(titulo: 'SOÑADORAS', subtitulo: 'cuota alta, más riesgo', icono: Icons.local_fire_department_rounded, color: c.ledger),
        if (sonadoras.isEmpty) const _SinOpciones(mensaje: 'Sin longshots con valor hoy.') else ...sonadoras.map((a) => tarjeta(a, c.ledger)),
      ],
    );
  }
}

class _CombinadasTab extends StatelessWidget {
  final List<CombinadaMismoPartido> fijas;
  final List<CombinadaMismoPartido> sonadoras;
  const _CombinadasTab({required this.fijas, required this.sonadoras});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    if (fijas.isEmpty && sonadoras.isEmpty) {
      return Center(child: Text('Sin combinadas de un mismo partido con valor hoy', style: TextStyle(color: c.textSecond)));
    }
    Widget tarjeta(CombinadaMismoPartido comb, Color acento) => InkWell(
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
                        style: AppTheme.score(c, size: 12).copyWith(color: acento)),
                  ]),
                ),
              const SizedBox(height: 6),
              Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                Text('Stake total: ${comb.stakeTotalPct.toStringAsFixed(1)}%',
                    style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.w600, color: c.text)),
                Text('EV ${(comb.evPortafolio * 100).toStringAsFixed(1)}%',
                    style: TextStyle(fontSize: 11.5, color: acento)),
              ]),
            ]),
          ),
        );
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _GrupoHeader(titulo: 'FIJAS', subtitulo: 'alta probabilidad, poco riesgo', icono: Icons.shield_rounded, color: c.pitch),
        if (fijas.isEmpty) const _SinOpciones(mensaje: 'Nada suficientemente seguro hoy.') else ...fijas.map((c2) => tarjeta(c2, c.pitch)),
        const SizedBox(height: 8),
        _GrupoHeader(titulo: 'SOÑADORAS', subtitulo: 'cuota alta, más riesgo', icono: Icons.local_fire_department_rounded, color: c.ledger),
        if (sonadoras.isEmpty) const _SinOpciones(mensaje: 'Sin longshots con valor hoy.') else ...sonadoras.map((c2) => tarjeta(c2, c.ledger)),
      ],
    );
  }
}

class _ParlaysTab extends StatelessWidget {
  final List<ParlaySugerido> fijas;
  final List<ParlaySugerido> sonadoras;
  const _ParlaysTab({required this.fijas, required this.sonadoras});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    if (fijas.isEmpty && sonadoras.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text('Necesitás 2+ partidos con value bet hoy para armar una combinada',
              style: TextStyle(color: c.textSecond), textAlign: TextAlign.center),
        ),
      );
    }
    Widget tarjeta(ParlaySugerido p, Color acento) => Container(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: c.surface,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: c.line),
          ),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('COMBINADA DE ${p.nPatas} PATAS', style: AppTheme.eyebrow(c, color: acento)),
            const SizedBox(height: 10),
            for (final pata in p.selecciones)
              Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Row(children: [
                  Container(width: 3, height: 22, decoration: BoxDecoration(color: acento, borderRadius: BorderRadius.circular(2))),
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
              _dato(c, 'Stake', '${p.stakePct.toStringAsFixed(1)}%', destacar: true, acento: acento),
              _dato(c, 'EV', '${(p.ev * 100).toStringAsFixed(0)}%', destacar: true, acento: acento),
            ]),
          ]),
        );
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _GrupoHeader(titulo: 'FIJAS', subtitulo: 'patas de mayor probabilidad', icono: Icons.shield_rounded, color: c.pitch),
        if (fijas.isEmpty) const _SinOpciones(mensaje: 'Nada suficientemente seguro hoy.') else ...fijas.map((p) => tarjeta(p, c.pitch)),
        const SizedBox(height: 8),
        _GrupoHeader(titulo: 'SOÑADORAS', subtitulo: 'patas de mayor cuota', icono: Icons.local_fire_department_rounded, color: c.ledger),
        if (sonadoras.isEmpty) const _SinOpciones(mensaje: 'Sin combinadas jugosas hoy.') else ...sonadoras.map((p) => tarjeta(p, c.ledger)),
      ],
    );
  }

  Widget _dato(AppColors c, String label, String valor, {bool destacar = false, Color? acento}) {
    return Column(children: [
      Text(valor, style: AppTheme.score(c, size: 14).copyWith(color: destacar ? (acento ?? c.pitch) : c.text)),
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
