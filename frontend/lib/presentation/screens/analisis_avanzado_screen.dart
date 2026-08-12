import 'package:flutter/material.dart';
import '../../core/theme.dart';
import '../../core/errors/failures.dart';
import '../../domain/entities/analisis_avanzado.dart';
import '../../domain/usecases/get_kelly_portafolio.dart';
import '../../domain/usecases/get_kelly_mercados.dart';
import '../../domain/usecases/get_jugadores_partido.dart';
import '../../domain/usecases/guardar_mercados.dart';
import '../../data/repositories/analisis_repo_impl.dart';
import '../widgets/clay.dart';

class AnalisisAvanzadoScreen extends StatefulWidget {
  final int partidoId;
  const AnalisisAvanzadoScreen({super.key, required this.partidoId});

  @override
  State<AnalisisAvanzadoScreen> createState() => _AnalisisAvanzadoScreenState();
}

class _AnalisisAvanzadoScreenState extends State<AnalisisAvanzadoScreen> {
  late final GetKellyMercados _getMercados;
  late final GetKellyPortafolio _getPortafolio;
  late final GetJugadoresPartido _getJugadores;

  KellyAnalisis? _mercados;
  KellyPortafolio? _portafolio;
  JugadoresPartido? _jugadores;
  bool _cargando = true;
  Failure? _errorMercados;
  Failure? _errorPortafolio;
  Failure? _errorJugadores;

  @override
  void initState() {
    super.initState();
    final repo = AnalisisRepositoryImpl.create();
    _getMercados = GetKellyMercados(repo);
    _getPortafolio = GetKellyPortafolio(repo);
    _getJugadores = GetJugadoresPartido(repo);
    _cargar();
  }

  Future<void> _cargar() async {
    final futureMercados = _getMercados(widget.partidoId);
    final futurePortafolio = _getPortafolio(widget.partidoId);
    final futureJugadores = _getJugadores(widget.partidoId);
    final rMercados = await futureMercados;
    final rPortafolio = await futurePortafolio;
    final rJugadores = await futureJugadores;
    setState(() {
      _mercados = rMercados.kelly;
      _errorMercados = rMercados.error;
      _portafolio = rPortafolio.portafolio;
      _errorPortafolio = rPortafolio.error;
      _jugadores = rJugadores.jugadores;
      _errorJugadores = rJugadores.error;
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
          title: const Text('Análisis avanzado', style: TextStyle(fontSize: 15)),
          bottom: TabBar(
            isScrollable: true,
            indicatorColor: c.pitch,
            labelColor: c.pitch,
            unselectedLabelColor: c.textSecond,
            tabs: const [
              Tab(text: 'TODOS LOS MERCADOS'),
              Tab(text: 'KELLY PORTAFOLIO'),
              Tab(text: 'JUGADORES'),
            ],
          ),
        ),
        body: _cargando
            ? Center(child: CircularProgressIndicator(color: c.pitch))
            : TabBarView(
                children: [
                  _MercadosTab(partidoId: widget.partidoId, kelly: _mercados, error: _errorMercados),
                  _PortafolioTab(portafolio: _portafolio, error: _errorPortafolio),
                  _JugadoresTab(jugadores: _jugadores, error: _errorJugadores),
                ],
              ),
      ),
    );
  }
}

class _MercadosTab extends StatefulWidget {
  final int partidoId;
  final KellyAnalisis? kelly;
  final Failure? error;
  const _MercadosTab({required this.partidoId, required this.kelly, required this.error});

  @override
  State<_MercadosTab> createState() => _MercadosTabState();
}

class _MercadosTabState extends State<_MercadosTab> {
  bool _soloValor = false;
  final Set<String> _seleccionadas = {};
  bool _guardando = false;
  String? _mensajeGuardado;

  Future<void> _guardar() async {
    setState(() { _guardando = true; _mensajeGuardado = null; });
    final usecase = GuardarMercados(AnalisisRepositoryImpl.create());
    final r = await usecase(widget.partidoId, _seleccionadas.toList());
    setState(() {
      _guardando = false;
      if (r.error != null) {
        _mensajeGuardado = r.error!.mensaje;
      } else {
        _mensajeGuardado = '${r.guardados!.length} predicción(es) guardada(s) — se cierra sola cuando termine el partido';
        _seleccionadas.clear();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    if (widget.error != null) return _MensajeError(widget.error!.mensaje);
    final k = widget.kelly!;
    if (k.todosMercados.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text('Sin mercados calculables — falta historial o cuotas guardadas.',
              style: TextStyle(color: c.textSecond), textAlign: TextAlign.center),
        ),
      );
    }
    final visibles = _soloValor ? k.todosMercados.where((m) => m.esValueBet).toList() : k.todosMercados;
    return Column(children: [
      Padding(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
        child: Row(children: [
          Text('${k.nValueBets} con valor de ${k.todosMercados.length} mercados',
              style: TextStyle(fontSize: 12, color: c.textSecond)),
          const Spacer(),
          FilterChip(
            label: const Text('Solo con valor'),
            selected: _soloValor,
            onSelected: (v) => setState(() => _soloValor = v),
            labelStyle: TextStyle(fontSize: 11.5, color: _soloValor ? c.bg : c.textSecond),
            selectedColor: c.pitch,
            backgroundColor: c.bg2,
            side: BorderSide.none,
          ),
        ]),
      ),
      Expanded(
        child: _MercadosPorCategoria(
          mercados: visibles,
          seleccionadas: _seleccionadas,
          onToggle: (clave) => setState(() {
            if (!_seleccionadas.add(clave)) _seleccionadas.remove(clave);
          }),
        ),
      ),
      if (_mensajeGuardado != null)
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
          child: Text(_mensajeGuardado!, style: TextStyle(fontSize: 11.5, color: c.textSecond), textAlign: TextAlign.center),
        ),
      if (_seleccionadas.isNotEmpty)
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
          child: ClayButton(
            label: 'Guardar predicción (${_seleccionadas.length})',
            icon: Icons.bookmark_added_outlined,
            loading: _guardando,
            onPressed: _guardar,
          ),
        ),
    ]);
  }
}

// Agrupa por categoría (mismo criterio que usa la casa de apuestas de
// referencia: Resultado / Hándicap / Goles / Corners / Tarjetas / 1er
// tiempo...) en vez de una lista plana de 20-30 filas — la cantidad de
// mercados no cambia, cambia que ahora se puede escanear.
class _MercadosPorCategoria extends StatelessWidget {
  final List<KellyMercado> mercados;
  final Set<String> seleccionadas;
  final ValueChanged<String> onToggle;
  const _MercadosPorCategoria({required this.mercados, required this.seleccionadas, required this.onToggle});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final porCategoria = <String, List<KellyMercado>>{};
    for (final m in mercados) {
      porCategoria.putIfAbsent(m.categoria, () => []).add(m);
    }
    final categorias = KellyMercado.ordenCategorias.where((cat) => porCategoria.containsKey(cat)).toList();

    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
      itemCount: categorias.length,
      itemBuilder: (_, i) {
        final categoria = categorias[i];
        final items = porCategoria[categoria]!;
        final valueBetsEnCategoria = items.where((m) => m.esValueBet).length;
        return Container(
          margin: const EdgeInsets.only(bottom: 10),
          decoration: BoxDecoration(
            color: c.surface,
            borderRadius: BorderRadius.circular(13),
            border: Border.all(color: c.line),
          ),
          child: Theme(
            data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
            child: ExpansionTile(
              initiallyExpanded: categoria == 'Resultado del partido',
              tilePadding: const EdgeInsets.symmetric(horizontal: 14),
              childrenPadding: const EdgeInsets.fromLTRB(10, 0, 10, 10),
              iconColor: c.textSecond,
              collapsedIconColor: c.textSecond,
              title: Row(children: [
                Expanded(child: Text(categoria, style: TextStyle(fontSize: 13.5, fontWeight: FontWeight.w600, color: c.text))),
                if (valueBetsEnCategoria > 0)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(color: c.pitchSoft, borderRadius: BorderRadius.circular(8)),
                    child: Text('$valueBetsEnCategoria con valor', style: TextStyle(fontSize: 10.5, color: c.pitch, fontWeight: FontWeight.w600)),
                  ),
              ]),
              children: [
                for (final m in items)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: _MercadoKellyRow(
                      m: m,
                      seleccionado: seleccionadas.contains(m.clave),
                      onToggleSeleccion: () => onToggle(m.clave),
                    ),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _MercadoKellyRow extends StatelessWidget {
  final KellyMercado m;
  final bool seleccionado;
  final VoidCallback onToggleSeleccion;
  const _MercadoKellyRow({required this.m, required this.seleccionado, required this.onToggleSeleccion});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    // checkbox y el resto de la fila son hermanos, no uno anidado dentro
    // del otro — dos InkWell/GestureDetector superpuestos en el mismo
    // tap compiten en la gesture arena y pueden disparar los dos a la
    // vez; como hermanos con áreas separadas, no hay ambigüedad.
    return Container(
      decoration: BoxDecoration(
        color: m.esValueBet ? c.pitchSoft : c.surface,
        borderRadius: BorderRadius.circular(13),
        border: Border.all(color: seleccionado ? c.ledger : (m.esValueBet ? c.pitch : c.line),
            width: seleccionado ? 1.5 : 1),
      ),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        InkWell(
          borderRadius: const BorderRadius.horizontal(left: Radius.circular(13)),
          onTap: onToggleSeleccion,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(13, 13, 10, 13),
            child: Icon(
              seleccionado ? Icons.check_circle_rounded : Icons.circle_outlined,
              size: 20, color: seleccionado ? c.ledger : c.textMuted,
            ),
          ),
        ),
        Expanded(
          child: InkWell(
            borderRadius: const BorderRadius.horizontal(right: Radius.circular(13)),
            onTap: () => _abrirDetalle(context, m),
            child: Padding(
              padding: const EdgeInsets.fromLTRB(0, 13, 13, 13),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                  Expanded(
                    child: Text(m.mercado, style: TextStyle(fontSize: 13.5, fontWeight: FontWeight.w600, color: c.text)),
                  ),
                  if (m.esValueBet)
                    Text('${m.stakePct.toStringAsFixed(1)}%',
                        style: AppTheme.score(c, size: 15).copyWith(color: c.pitch))
                  else
                    Text('sin valor', style: TextStyle(fontSize: 11, color: c.textMuted)),
                  const SizedBox(width: 6),
                  Icon(Icons.chevron_right_rounded, size: 18, color: c.textMuted),
                ]),
                const SizedBox(height: 6),
                Text(m.porQue, style: TextStyle(fontSize: 11.5, color: c.textSecond, height: 1.35)),
              ]),
            ),
          ),
        ),
      ]),
    );
  }
}

void _abrirDetalle(BuildContext context, KellyMercado m) {
  final c = context.colors;
  showModalBottomSheet(
    context: context,
    backgroundColor: c.surface,
    shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
    builder: (_) => Padding(
      padding: const EdgeInsets.fromLTRB(20, 10, 20, 28),
      child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
        Center(
          child: Container(width: 36, height: 4, margin: const EdgeInsets.only(bottom: 16),
              decoration: BoxDecoration(color: c.lineStrong, borderRadius: BorderRadius.circular(2))),
        ),
        Text(m.mercado, style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: c.text)),
        const SizedBox(height: 4),
        Text(m.esValueBet ? 'Value bet' : 'Sin valor', style: TextStyle(fontSize: 12.5, color: m.esValueBet ? c.pitch : c.textMuted, fontWeight: FontWeight.w600)),
        const SizedBox(height: 18),
        Row(children: [
          _detalleMetric('Probabilidad modelo', '${(m.probabilidad * 100).toStringAsFixed(1)}%', c),
          _detalleMetric('Prob. implícita', '${(m.probImplicita * 100).toStringAsFixed(1)}%', c),
        ]),
        const SizedBox(height: 14),
        Row(children: [
          _detalleMetric('Cuota del mercado', m.cuota.toStringAsFixed(2), c),
          _detalleMetric('Cuota justa (modelo)', m.cuotaJusta.toStringAsFixed(2), c),
        ]),
        const SizedBox(height: 14),
        Row(children: [
          _detalleMetric('Edge', '${(m.edge * 100).toStringAsFixed(1)}pp', c, destacar: m.edge > 0),
          _detalleMetric('EV', '${(m.ev * 100).toStringAsFixed(1)}%', c, destacar: m.ev > 0),
        ]),
        const SizedBox(height: 14),
        Row(children: [
          _detalleMetric('Stake sugerido', '${m.stakePct.toStringAsFixed(1)}%', c, destacar: m.esValueBet),
          _detalleMetric('Stake en unidades', m.stakeUnits.toStringAsFixed(2), c, destacar: m.esValueBet),
        ]),
        const SizedBox(height: 18),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(color: c.bg2, borderRadius: BorderRadius.circular(11)),
          child: Text(m.mensaje, style: TextStyle(fontSize: 12.5, color: c.textSecond, height: 1.4)),
        ),
      ]),
    ),
  );
}

Widget _detalleMetric(String label, String valor, AppColors c, {bool destacar = false}) {
  return Expanded(
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(label, style: TextStyle(fontSize: 10.5, color: c.textSecond)),
      const SizedBox(height: 3),
      Text(valor, style: AppTheme.score(c, size: 16).copyWith(color: destacar ? c.pitch : c.text)),
    ]),
  );
}

class _PortafolioTab extends StatelessWidget {
  final KellyPortafolio? portafolio;
  final Failure? error;
  const _PortafolioTab({required this.portafolio, required this.error});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    if (error != null) return _MensajeError(error!.mensaje);
    final p = portafolio!;
    if (p.sinEdge) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text('Sin edge positivo en ningún mercado — Kelly recomienda no apostar.',
              style: TextStyle(color: c.textSecond), textAlign: TextAlign.center),
        ),
      );
    }
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _Metric('Stake total', '${p.stakeTotalPct.toStringAsFixed(1)}%'),
                _Metric('Unidades', p.stakeTotalUnidades.toStringAsFixed(0)),
                _Metric('EV', '${(p.evPortafolio * 100).toStringAsFixed(1)}%'),
                _Metric('P(ruina)', '${(p.probabilidadRuina * 100).toStringAsFixed(0)}%',
                    color: p.probabilidadRuina > 0.2 ? c.brick : null),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),
        for (final m in p.mercados.where((m) => m.stakePct > 0))
          Card(
            child: ListTile(
              title: Text(m.nombre, style: TextStyle(color: c.text)),
              subtitle: Text(
                  'Cuota ${m.cuota.toStringAsFixed(2)} · Prob ${(m.probabilidad * 100).toStringAsFixed(0)}%',
                  style: TextStyle(color: c.textSecond, fontSize: 12)),
              trailing: Text('${m.stakePct.toStringAsFixed(1)}%',
                  style: AppTheme.score(c, size: 16).copyWith(color: c.pitch)),
            ),
          ),
      ],
    );
  }
}

class _JugadoresTab extends StatelessWidget {
  final JugadoresPartido? jugadores;
  final Failure? error;
  const _JugadoresTab({required this.jugadores, required this.error});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    if (error != null) return _MensajeError(error!.mensaje);
    final j = jugadores!;
    if (j.vacio) {
      return Center(
        child: Text('Sin XI probable estimable (falta historial reciente).',
            style: TextStyle(color: c.textSecond)),
      );
    }
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (j.local.isNotEmpty) _EquipoSeccion('LOCAL', j.local),
        if (j.visitante.isNotEmpty) _EquipoSeccion('VISITANTE', j.visitante),
      ],
    );
  }
}

class _EquipoSeccion extends StatelessWidget {
  final String titulo;
  final List<JugadorMercado> jugadores;
  const _EquipoSeccion(this.titulo, this.jugadores);

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 8, top: 8),
          child: Text(titulo, style: AppTheme.eyebrow(c)),
        ),
        Container(
          decoration: BoxDecoration(
            color: c.surface,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: c.line),
          ),
          child: Column(
            children: [
              for (var i = 0; i < jugadores.length; i++)
                _JugadorRow(jug: jugadores[i], ultimo: i == jugadores.length - 1),
            ],
          ),
        ),
        const SizedBox(height: 16),
      ],
    );
  }
}

// Fila compacta — el detalle completo (tiros/asistencias/pases/goles/
// tarjetas por pestaña) vive en el bottom sheet, mismo patrón que
// _abrirDetalle() para mercados. Evita 10 cards enormes siempre
// expandidas por equipo.
class _JugadorRow extends StatelessWidget {
  final JugadorMercado jug;
  final bool ultimo;
  const _JugadorRow({required this.jug, required this.ultimo});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return InkWell(
      onTap: () => _abrirDetalleJugador(context, jug),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          border: ultimo ? null : Border(bottom: BorderSide(color: c.line)),
        ),
        child: Row(children: [
          Container(
            width: 34, height: 34,
            decoration: BoxDecoration(color: c.pitchSoft, shape: BoxShape.circle),
            alignment: Alignment.center,
            child: Text(jug.inicial, style: AppTheme.score(c, size: 13).copyWith(color: c.pitch)),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(jug.nombre, style: TextStyle(color: c.text, fontWeight: FontWeight.w600, fontSize: 13.5)),
              const SizedBox(height: 2),
              Text('${jug.nPartidosHistorial} partidos de historial', style: TextStyle(fontSize: 10.5, color: c.textMuted)),
            ]),
          ),
          if (jug.posicion != null)
            Container(
              margin: const EdgeInsets.only(right: 8),
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(color: c.bg2, borderRadius: BorderRadius.circular(6)),
              child: Text(jug.posicion!, style: TextStyle(color: c.textSecond, fontSize: 10.5)),
            ),
          Icon(Icons.chevron_right_rounded, size: 18, color: c.textMuted),
        ]),
      ),
    );
  }
}

void _abrirDetalleJugador(BuildContext context, JugadorMercado jug) {
  final c = context.colors;
  showModalBottomSheet(
    context: context,
    backgroundColor: c.surface,
    isScrollControlled: true,
    shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
    builder: (_) => _JugadorDetalleSheet(jug: jug),
  );
}

class _JugadorDetalleSheet extends StatefulWidget {
  final JugadorMercado jug;
  const _JugadorDetalleSheet({required this.jug});

  @override
  State<_JugadorDetalleSheet> createState() => _JugadorDetalleSheetState();
}

class _JugadorDetalleSheetState extends State<_JugadorDetalleSheet> {
  int _tab = 0;

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final jug = widget.jug;
    const tabs = ['Estadísticas', 'Goles', 'Tarjetas'];

    return Padding(
      padding: EdgeInsets.fromLTRB(20, 10, 20, MediaQuery.of(context).viewInsets.bottom + 24),
      child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
        Center(
          child: Container(width: 36, height: 4, margin: const EdgeInsets.only(bottom: 16),
              decoration: BoxDecoration(color: c.lineStrong, borderRadius: BorderRadius.circular(2))),
        ),
        Row(children: [
          Container(
            width: 42, height: 42,
            decoration: BoxDecoration(color: c.pitchSoft, shape: BoxShape.circle),
            alignment: Alignment.center,
            child: Text(jug.inicial, style: AppTheme.score(c, size: 15).copyWith(color: c.pitch)),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(jug.nombre, style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: c.text)),
              Text('${jug.posicion ?? ''} · ${jug.nPartidosHistorial} partidos de historial',
                  style: TextStyle(fontSize: 11.5, color: c.textSecond)),
            ]),
          ),
        ]),
        const SizedBox(height: 18),
        Row(
          children: List.generate(tabs.length, (i) {
            final activo = _tab == i;
            return Padding(
              padding: const EdgeInsets.only(right: 8),
              child: GestureDetector(
                onTap: () => setState(() => _tab = i),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 8),
                  decoration: BoxDecoration(
                    color: activo ? c.pitch : c.bg2,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(tabs[i], style: TextStyle(fontSize: 12, color: activo ? c.bg : c.textSecond,
                      fontWeight: activo ? FontWeight.w600 : FontWeight.normal)),
                ),
              ),
            );
          }),
        ),
        const SizedBox(height: 16),
        if (_tab == 0) ..._panelEstadisticas(c, jug),
        if (_tab == 1) ..._panelGoles(c, jug),
        if (_tab == 2) ..._panelTarjetas(c, jug),
      ]),
    );
  }

  List<Widget> _panelEstadisticas(AppColors c, JugadorMercado jug) => [
        Row(children: [
          _statBox(c, 'Tiros', jug.tirosPromedio.toStringAsFixed(1)),
          _statBox(c, 'Al arco', jug.tirosArcoPromedio.toStringAsFixed(1)),
          _statBox(c, 'Asist.', jug.asistenciasPromedio.toStringAsFixed(1)),
          _statBox(c, 'Pases', jug.pasesPromedio.toStringAsFixed(0)),
        ]),
        const SizedBox(height: 4),
        _bloqueMercado(c, 'Tiros', jug.tirosOverUnder),
        _bloqueMercado(c, 'Tiros al arco', jug.tirosArcoOverUnder),
        _bloqueMercado(c, 'Asistencias', jug.asistenciasOverUnder),
        _bloqueMercado(c, 'Pases', jug.pasesOverUnder),
        _bloqueMercado(c, 'Entradas', jug.entradasOverUnder),
      ];

  List<Widget> _panelGoles(AppColors c, JugadorMercado jug) => [
        Row(children: [
          _statBox(c, 'Prob. anota', '${(jug.probAnota * 100).toStringAsFixed(0)}%', destacar: jug.probAnota >= 0.4),
        ]),
        const SizedBox(height: 4),
        _bloqueMercado(c, 'Anota', jug.golesOverUnder, etiquetaCorta: true),
      ];

  List<Widget> _panelTarjetas(AppColors c, JugadorMercado jug) => [
        Row(children: [
          _statBox(c, 'Amarilla', '${(jug.probAmarilla * 100).toStringAsFixed(0)}%'),
          _statBox(c, 'Roja', '${(jug.probRoja * 100).toStringAsFixed(0)}%', destacar: jug.probRoja > 0.05),
        ]),
      ];

  Widget _statBox(AppColors c, String label, String valor, {bool destacar = false}) {
    return Expanded(
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(valor, style: AppTheme.score(c, size: 16).copyWith(color: destacar ? c.pitch : c.text)),
        const SizedBox(height: 2),
        Text(label, style: TextStyle(fontSize: 10.5, color: c.textSecond)),
      ]),
    );
  }

  Widget _bloqueMercado(AppColors c, String etiqueta, Map<String, double> ou, {bool etiquetaCorta = false}) {
    if (ou.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(top: 14),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(etiqueta.toUpperCase(), style: AppTheme.eyebrow(c)),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8, runSpacing: 8,
          children: ou.entries.map((e) {
            final linea = e.key.replaceFirst('over_', '').replaceAll('_', '.');
            final texto = etiquetaCorta ? '$linea+' : '+$linea';
            return Container(
              width: 78,
              padding: const EdgeInsets.symmetric(vertical: 8),
              decoration: BoxDecoration(
                color: e.value >= 0.5 ? c.pitchSoft : c.bg2,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: e.value >= 0.5 ? c.pitch : c.line),
              ),
              child: Column(children: [
                Text(texto, style: TextStyle(fontSize: 10.5, color: c.textSecond)),
                const SizedBox(height: 3),
                Text('${(e.value * 100).toStringAsFixed(0)}%',
                    style: AppTheme.score(c, size: 14).copyWith(color: e.value >= 0.5 ? c.pitch : c.text)),
              ]),
            );
          }).toList(),
        ),
      ]),
    );
  }
}

class _Metric extends StatelessWidget {
  final String label;
  final String valor;
  final Color? color;
  const _Metric(this.label, this.valor, {this.color});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Column(
      children: [
        Text(valor, style: TextStyle(color: color ?? c.text, fontSize: 16, fontWeight: FontWeight.w700)),
        Text(label, style: TextStyle(color: c.textSecond, fontSize: 11)),
      ],
    );
  }
}

class _MensajeError extends StatelessWidget {
  final String mensaje;
  const _MensajeError(this.mensaje);

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Text(mensaje, style: TextStyle(color: c.textSecond), textAlign: TextAlign.center),
      ),
    );
  }
}
