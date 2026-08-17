import 'dart:async';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../core/theme.dart';
import '../../core/product_analytics.dart';
import '../../core/errors/failures.dart';
import '../../domain/entities/recomendadas.dart';
import '../../domain/entities/parlay.dart';
import '../../domain/usecases/get_recomendadas.dart';
import '../../data/repositories/partido_repo_impl.dart';
import '../widgets/app_bottom_nav.dart';
import '../widgets/clay.dart';
import '../widgets/design_system.dart';
import '../widgets/team_logo.dart';
import '../providers/prediction_coupon_provider.dart';

class RecomendadasScreen extends StatefulWidget {
  const RecomendadasScreen({super.key});

  @override
  State<RecomendadasScreen> createState() => _RecomendadasScreenState();
}

class _RecomendadasScreenState extends State<RecomendadasScreen>
    with WidgetsBindingObserver {
  late final GetRecomendadas _getRecomendadas;
  Recomendadas? _datos;
  bool _cargando = true;
  Failure? _error;
  Timer? _autoRefresh;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    ProductAnalytics.track('screen_view', {'screen': 'oportunidades'});
    _getRecomendadas = GetRecomendadas(PartidoRepositoryImpl.create());
    _cargar();
    _autoRefresh = Timer.periodic(
      const Duration(seconds: 60),
      (_) => _cargar(mostrarCargando: false),
    );
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _cargar(mostrarCargando: false);
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _autoRefresh?.cancel();
    super.dispose();
  }

  Future<void> _cargar({bool mostrarCargando = true}) async {
    if (mostrarCargando && mounted) setState(() => _cargando = true);
    final r = await _getRecomendadas();
    if (!mounted) return;
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
      length: 4,
      child: Scaffold(
        appBar: AppHeader(
          title: 'Oportunidades',
          subtitle: 'Valor detectado por modelo y mercado',
          actions: [
            IconButton(
                icon: Icon(Icons.refresh, color: c.textSecond),
                onPressed: _cargar)
          ],
        ),
        body: Column(children: [
          if (!_cargando && _error == null)
            TabBar(
              isScrollable: true,
              indicatorColor: c.pitch,
              labelColor: c.pitch,
              unselectedLabelColor: c.textSecond,
              tabs: [
                Tab(
                    text:
                        'INDIVIDUALES (${(_datos?.individualesFijas.length ?? 0) + (_datos?.individualesSonadoras.length ?? 0)})'),
                Tab(
                    text:
                        'JUGADORES (${(_datos?.jugadoresFijas.length ?? 0) + (_datos?.jugadoresSonadoras.length ?? 0)})'),
                Tab(
                    text:
                        'CORRELACIONADAS (${(_datos?.combinadasFijas.length ?? 0) + (_datos?.combinadasSonadoras.length ?? 0)})'),
                Tab(
                    text:
                        'PORTAFOLIOS (${(_datos?.parlaysFijas.length ?? 0) + (_datos?.parlaysSonadoras.length ?? 0)})'),
              ],
            ),
          Expanded(
              child: _cargando
                  ? Center(child: CircularProgressIndicator(color: c.pitch))
                  : _error != null
                      ? _MensajeError(
                          mensaje: _error!.mensaje, onRetry: _cargar)
                      : _datos!.vacio
                          ? Center(
                              child: Padding(
                                padding: const EdgeInsets.all(24),
                                child: Text(
                                    'Sin recomendaciones para hoy — falta historial o cuotas guardadas en los partidos del día.',
                                    style: TextStyle(color: c.textSecond),
                                    textAlign: TextAlign.center),
                              ),
                            )
                          : TabBarView(children: [
                              _IndividualesTab(
                                  fijas: _datos!.individualesFijas,
                                  sonadoras: _datos!.individualesSonadoras),
                              _JugadoresRecomendadosTab(
                                  fijas: _datos!.jugadoresFijas,
                                  sonadoras: _datos!.jugadoresSonadoras),
                              _CombinadasTab(
                                  fijas: _datos!.combinadasFijas,
                                  sonadoras: _datos!.combinadasSonadoras),
                              _ParlaysTab(
                                  fijas: _datos!.parlaysFijas,
                                  sonadoras: _datos!.parlaysSonadoras),
                            ])),
        ]),
        floatingActionButton: FloatingActionButton.extended(
          onPressed: () => context.push('/parlay'),
          icon: const Icon(Icons.add_circle_outline_rounded),
          label: const Text('Crear parlay'),
        ),
        bottomNavigationBar: const AppBottomNav(current: AppTab.oportunidades),
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
  const _GrupoHeader(
      {required this.titulo,
      required this.subtitulo,
      required this.icono,
      required this.color});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Padding(
      padding: const EdgeInsets.fromLTRB(2, 4, 2, 10),
      child: Row(children: [
        Icon(icono, size: 15, color: color),
        const SizedBox(width: 6),
        Text(titulo,
            style: TextStyle(
                fontSize: 12.5,
                fontWeight: FontWeight.w700,
                color: color,
                letterSpacing: 0.3)),
        const SizedBox(width: 6),
        Expanded(
            child: Text(subtitulo,
                style: TextStyle(fontSize: 10.5, color: c.textMuted))),
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

class _IndividualesTab extends StatefulWidget {
  final List<ApuestaIndividual> fijas;
  final List<ApuestaIndividual> sonadoras;
  const _IndividualesTab({required this.fijas, required this.sonadoras});

  @override
  State<_IndividualesTab> createState() => _IndividualesTabState();
}

class _IndividualesTabState extends State<_IndividualesTab> {
  String? _liga;
  String _estado = 'Todos';

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    if (widget.fijas.isEmpty && widget.sonadoras.isEmpty) {
      return Center(
          child: Text('Sin value bets hoy',
              style: TextStyle(color: c.textSecond)));
    }

    final todas = <({ApuestaIndividual apuesta, bool fija})>[
      ...widget.fijas.map((a) => (apuesta: a, fija: true)),
      ...widget.sonadoras.map((a) => (apuesta: a, fija: false)),
    ];
    final ligas = todas.map((e) => e.apuesta.liga).toSet().toList()..sort();
    final filtradas = todas.where((e) {
      final a = e.apuesta;
      if (_liga != null && a.liga != _liga) return false;
      if (_estado == 'Pendientes' && a.resuelta) return false;
      if (_estado == 'En vivo' && !a.enJuego) return false;
      if (_estado == 'Resueltas' && !a.resuelta) return false;
      return true;
    });
    final porPartido = <int, List<({ApuestaIndividual apuesta, bool fija})>>{};
    for (final item in filtradas) {
      porPartido.putIfAbsent(item.apuesta.partidoId, () => []).add(item);
    }

    Widget mercado(({ApuestaIndividual apuesta, bool fija}) item) {
      final a = item.apuesta;
      final resuelta = a.resuelta;
      final gano = a.acerto == true;
      final acento =
          item.fija ? c.pitch : Theme.of(context).colorScheme.tertiary;
      return Opacity(
        opacity: resuelta ? .68 : 1,
        child: Container(
          margin: const EdgeInsets.fromLTRB(12, 0, 12, 10),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: c.bg2,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
                color: resuelta ? (gano ? c.pitch : c.brick) : c.line),
          ),
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                decoration: BoxDecoration(
                    color: acento.withValues(alpha: .14),
                    borderRadius: BorderRadius.circular(6)),
                child: Text(item.fija ? 'FIJA' : 'SOÑADORA',
                    style: AppTheme.eyebrow(c, color: acento)),
              ),
              const SizedBox(width: 8),
              Expanded(
                  child: Text(a.mercado,
                      style: TextStyle(
                        color: c.text,
                        fontWeight: FontWeight.w700,
                        decoration:
                            resuelta ? TextDecoration.lineThrough : null,
                      ))),
              Text(
                  resuelta
                      ? (gano ? 'ACERTÓ' : 'FALLÓ')
                      : a.cuota.toStringAsFixed(2),
                  style: TextStyle(
                      color: resuelta ? (gano ? c.pitch : c.brick) : acento,
                      fontWeight: FontWeight.w800)),
              if (!resuelta) ...[
                const SizedBox(width: 6),
                IconButton(
                  tooltip: 'Agregar al cupón',
                  visualDensity: VisualDensity.compact,
                  onPressed: () => context
                      .read<PredictionCouponProvider>()
                      .toggle(CouponSelection(
                        input: ParlaySeleccionInput(
                            partidoId: a.partidoId,
                            mercado: a.mercado,
                            cuota: a.cuota),
                        partido: '${a.local} vs ${a.visitante}',
                        liga: a.liga,
                        mercado: a.mercado,
                        probabilidad: a.probabilidad,
                      )),
                  icon: const Icon(Icons.add_circle_outline_rounded),
                ),
              ],
            ]),
            const SizedBox(height: 7),
            Text(a.porQue,
                style: TextStyle(
                    fontSize: 11.5, color: c.textSecond, height: 1.35)),
          ]),
        ),
      );
    }

    return Column(
      children: [
        SizedBox(
          height: 48,
          child: ListView(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            scrollDirection: Axis.horizontal,
            children: [
              _FilterPill(
                  label: 'Todas las ligas',
                  selected: _liga == null,
                  onTap: () => setState(() => _liga = null)),
              const SizedBox(width: 7),
              for (final liga in ligas) ...[
                _FilterPill(
                    label: liga,
                    selected: _liga == liga,
                    onTap: () => setState(() => _liga = liga)),
                const SizedBox(width: 7),
              ],
            ],
          ),
        ),
        SizedBox(
          height: 43,
          child: ListView(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 3),
            scrollDirection: Axis.horizontal,
            children: [
              for (final estado in const [
                'Todos',
                'Pendientes',
                'En vivo',
                'Resueltas'
              ]) ...[
                _FilterPill(
                    label: estado,
                    selected: _estado == estado,
                    onTap: () => setState(() => _estado = estado)),
                const SizedBox(width: 7),
              ],
            ],
          ),
        ),
        Expanded(
          child: porPartido.isEmpty
              ? Center(
                  child: Text('No hay oportunidades con estos filtros',
                      style: TextStyle(color: c.textSecond)))
              : ListView(
                  padding: const EdgeInsets.fromLTRB(12, 6, 12, 20),
                  children: [
                    for (final grupo in porPartido.values)
                      Card(
                        margin: const EdgeInsets.only(bottom: 10),
                        clipBehavior: Clip.antiAlias,
                        child: ExpansionTile(
                          initiallyExpanded: porPartido.length <= 3,
                          leading: SizedBox(
                            width: 50,
                            child: Stack(children: [
                              Positioned(
                                  left: 0,
                                  child: TeamLogo(
                                      url: grupo.first.apuesta.localLogo,
                                      nombre: grupo.first.apuesta.local,
                                      size: 30)),
                              Positioned(
                                  left: 20,
                                  child: TeamLogo(
                                      url: grupo.first.apuesta.visitanteLogo,
                                      nombre: grupo.first.apuesta.visitante,
                                      size: 30)),
                            ]),
                          ),
                          title: Text(
                              '${grupo.first.apuesta.local} — ${grupo.first.apuesta.visitante}',
                              maxLines: 2,
                              style: const TextStyle(
                                  fontSize: 13.5, fontWeight: FontWeight.w700)),
                          subtitle: Text(
                              '${grupo.first.apuesta.liga} · ${grupo.length} mercados',
                              style:
                                  TextStyle(fontSize: 11, color: c.textSecond)),
                          children: [
                            ...grupo.where((e) => e.fija).map(mercado),
                            ...grupo.where((e) => !e.fija).map(mercado),
                            Padding(
                              padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
                              child: OutlinedButton.icon(
                                onPressed: () => context.push(
                                    '/partido/${grupo.first.apuesta.partidoId}/avanzado'),
                                icon: const Icon(Icons.analytics_outlined),
                                label: const Text(
                                    'Fijas y soñadoras de jugadores'),
                              ),
                            ),
                          ],
                        ),
                      ),
                  ],
                ),
        ),
      ],
    );
  }
}

class _FilterPill extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;
  const _FilterPill(
      {required this.label, required this.selected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(18),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14),
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: selected ? c.pitchSoft : Colors.transparent,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: selected ? c.pitch : c.lineStrong),
        ),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          if (selected) ...[
            Icon(Icons.check_rounded, size: 15, color: c.pitch),
            const SizedBox(width: 5)
          ],
          Text(label,
              style: TextStyle(
                  color: selected ? c.pitch : c.textSecond,
                  fontSize: 12,
                  fontWeight: selected ? FontWeight.w700 : FontWeight.w500)),
        ]),
      ),
    );
  }
}

class _JugadoresRecomendadosTab extends StatelessWidget {
  final List<PronosticoJugador> fijas;
  final List<PronosticoJugador> sonadoras;
  const _JugadoresRecomendadosTab(
      {required this.fijas, required this.sonadoras});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final todos = [...fijas, ...sonadoras];
    if (todos.isEmpty) {
      return Center(
          child: Text('Sin jugadores con historial suficiente hoy',
              style: TextStyle(color: c.textSecond)));
    }
    final porPartido = <int, List<PronosticoJugador>>{};
    for (final item in todos) {
      porPartido.putIfAbsent(item.partidoId, () => []).add(item);
    }
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: Text(
            'Probabilidades del modelo. Ingresa la cuota de tu casa al crear el parlay para calcular valor y Kelly.',
            style: TextStyle(fontSize: 11.5, color: c.textSecond),
          ),
        ),
        for (final grupo in porPartido.values)
          Container(
            margin: const EdgeInsets.only(bottom: 12),
            decoration: BoxDecoration(
              color: c.surface,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: c.line),
            ),
            child: ExpansionTile(
              leading: Row(mainAxisSize: MainAxisSize.min, children: [
                TeamLogo(
                    url: grupo.first.localLogo,
                    nombre: grupo.first.local,
                    size: 24),
                Transform.translate(
                  offset: const Offset(-5, 0),
                  child: TeamLogo(
                      url: grupo.first.visitanteLogo,
                      nombre: grupo.first.visitante,
                      size: 24),
                ),
              ]),
              title: Text('${grupo.first.local} — ${grupo.first.visitante}',
                  style: TextStyle(fontWeight: FontWeight.w700, color: c.text)),
              subtitle: Text('${grupo.first.liga} · ${grupo.length} mercados',
                  style: TextStyle(fontSize: 11, color: c.textSecond)),
              children: [
                for (final item in grupo)
                  ListTile(
                    onTap: () => _agregarJugador(context, item),
                    leading: CircleAvatar(
                      backgroundColor: c.ledgerSoft,
                      child: Text(item.jugador.isEmpty ? '?' : item.jugador[0],
                          style: TextStyle(color: c.ledger)),
                    ),
                    title: Text(item.mercado,
                        style: TextStyle(fontSize: 12.5, color: c.text)),
                    subtitle: Text(
                        '${item.nPartidosHistorial} partidos de historial',
                        style: TextStyle(fontSize: 10.5, color: c.textMuted)),
                    trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                      Text('${(item.probabilidad * 100).toStringAsFixed(0)}%',
                          style: AppTheme.score(c, size: 14)
                              .copyWith(color: c.pitch)),
                      const SizedBox(width: 8),
                      const Icon(Icons.add_circle_outline_rounded, size: 20),
                    ]),
                  ),
              ],
            ),
          ),
      ],
    );
  }
}

Future<void> _agregarJugador(
    BuildContext context, PronosticoJugador item) async {
  final controller = TextEditingController();
  final cuota = await showDialog<double>(
    context: context,
    builder: (dialogContext) => AlertDialog(
      title: const Text('Cuota informativa'),
      content: TextField(
        controller: controller,
        autofocus: true,
        keyboardType: const TextInputType.numberWithOptions(decimal: true),
        decoration: InputDecoration(labelText: item.mercado, hintText: 'Ej. 1.85'),
      ),
      actions: [
        TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancelar')),
        FilledButton(
          onPressed: () {
            final value = double.tryParse(controller.text.replaceAll(',', '.'));
            if (value != null && value > 1) Navigator.pop(dialogContext, value);
          },
          child: const Text('Agregar'),
        ),
      ],
    ),
  );
  controller.dispose();
  if (cuota == null || !context.mounted) return;
  context.read<PredictionCouponProvider>().toggle(CouponSelection(
        input: ParlaySeleccionInput(
            partidoId: item.partidoId, mercado: item.clave, cuota: cuota),
        partido: '${item.local} vs ${item.visitante}',
        liga: item.liga,
        mercado: item.mercado,
        probabilidad: item.probabilidad,
      ));
}

class _CombinadasTab extends StatelessWidget {
  final List<CombinadaMismoPartido> fijas;
  final List<CombinadaMismoPartido> sonadoras;
  const _CombinadasTab({required this.fijas, required this.sonadoras});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    if (fijas.isEmpty && sonadoras.isEmpty) {
      return Center(
          child: Text('Sin combinadas de un mismo partido con valor hoy',
              style: TextStyle(color: c.textSecond)));
    }
    Widget tarjeta(CombinadaMismoPartido comb, Color acento) => InkWell(
          onTap: () => context.push('/partido/${comb.partidoId}/avanzado'),
          borderRadius: BorderRadius.circular(14),
          child: ClayContainer(
            padding: const EdgeInsets.all(15),
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                Expanded(
                  child: Text('${comb.local} vs ${comb.visitante}',
                      style: TextStyle(
                          fontSize: 13.5,
                          fontWeight: FontWeight.w600,
                          color: c.text)),
                ),
                Text(comb.liga,
                    style: TextStyle(fontSize: 10.5, color: c.textMuted)),
              ]),
              const SizedBox(height: 10),
              for (final m in comb.mercados)
                Padding(
                  padding: const EdgeInsets.only(bottom: 5),
                  child: Row(children: [
                    Expanded(
                        child: Text(m.nombre,
                            style:
                                TextStyle(fontSize: 12, color: c.textSecond))),
                    Text('${m.stakePct.toStringAsFixed(1)}%',
                        style: AppTheme.score(c, size: 12)
                            .copyWith(color: acento)),
                  ]),
                ),
              const SizedBox(height: 6),
              Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                Text('Stake total: ${comb.stakeTotalPct.toStringAsFixed(1)}%',
                    style: TextStyle(
                        fontSize: 11.5,
                        fontWeight: FontWeight.w600,
                        color: c.text)),
                Text('EV ${(comb.evPortafolio * 100).toStringAsFixed(1)}%',
                    style: TextStyle(fontSize: 11.5, color: acento)),
              ]),
            ]),
          ),
        );
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _GrupoHeader(
            titulo: 'RIESGO CONTROLADO',
            subtitulo: 'mayor probabilidad del modelo',
            icono: Icons.shield_rounded,
            color: c.ledger),
        if (fijas.isEmpty)
          const _SinOpciones(mensaje: 'Nada suficientemente seguro hoy.')
        else
          ...fijas.map((c2) => tarjeta(c2, c.pitch)),
        const SizedBox(height: 8),
        _GrupoHeader(
            titulo: 'RIESGO ALTO',
            subtitulo: 'mayor cuota y varianza',
            icono: Icons.warning_amber_rounded,
            color: Theme.of(context).colorScheme.tertiary),
        if (sonadoras.isEmpty)
          const _SinOpciones(mensaje: 'Sin longshots con valor hoy.')
        else
          ...sonadoras.map((c2) => tarjeta(c2, c.ledger)),
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
          child: Text(
              'Se necesitan 2+ partidos con valor esperado para crear una combinada',
              style: TextStyle(color: c.textSecond),
              textAlign: TextAlign.center),
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
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('COMBINADA DE ${p.nPatas} PATAS',
                style: AppTheme.eyebrow(c, color: acento)),
            const SizedBox(height: 10),
            for (final pata in p.selecciones)
              Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Row(children: [
                  Container(
                      width: 3,
                      height: 22,
                      decoration: BoxDecoration(
                          color: acento,
                          borderRadius: BorderRadius.circular(2))),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('${pata.local} vs ${pata.visitante}',
                              style: TextStyle(
                                  fontSize: 11.5, color: c.textSecond)),
                          Text(pata.mercado,
                              style: TextStyle(
                                  fontSize: 12.5,
                                  fontWeight: FontWeight.w600,
                                  color: c.text)),
                        ]),
                  ),
                ]),
              ),
            const Divider(height: 18),
            Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
              _dato(c, 'Cuota', p.cuotaCombinada.toStringAsFixed(2)),
              _dato(
                  c, 'Prob', '${(p.probCombinada * 100).toStringAsFixed(1)}%'),
              _dato(c, 'Stake', '${p.stakePct.toStringAsFixed(1)}%',
                  destacar: true, acento: acento),
              _dato(c, 'EV', '${(p.ev * 100).toStringAsFixed(0)}%',
                  destacar: true, acento: acento),
            ]),
          ]),
        );
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _GrupoHeader(
            titulo: 'RIESGO CONTROLADO',
            subtitulo: 'selecciones de mayor probabilidad',
            icono: Icons.shield_rounded,
            color: c.ledger),
        if (fijas.isEmpty)
          const _SinOpciones(mensaje: 'Nada suficientemente seguro hoy.')
        else
          ...fijas.map((p) => tarjeta(p, c.pitch)),
        const SizedBox(height: 8),
        _GrupoHeader(
            titulo: 'RIESGO ALTO',
            subtitulo: 'selecciones de mayor cuota',
            icono: Icons.warning_amber_rounded,
            color: Theme.of(context).colorScheme.tertiary),
        if (sonadoras.isEmpty)
          const _SinOpciones(mensaje: 'Sin combinadas de alto valor hoy.')
        else
          ...sonadoras.map((p) => tarjeta(p, c.ledger)),
      ],
    );
  }

  Widget _dato(AppColors c, String label, String valor,
      {bool destacar = false, Color? acento}) {
    return Column(children: [
      Text(valor,
          style: AppTheme.score(c, size: 14)
              .copyWith(color: destacar ? (acento ?? c.pitch) : c.text)),
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
          Text(mensaje,
              style: TextStyle(color: c.brick), textAlign: TextAlign.center),
          const SizedBox(height: 12),
          OutlinedButton(
            onPressed: onRetry,
            style: OutlinedButton.styleFrom(
                foregroundColor: c.brick, side: BorderSide(color: c.brick)),
            child: const Text('Reintentar'),
          ),
        ]),
      ),
    );
  }
}
