import 'package:flutter/material.dart';
import '../../core/theme.dart';
import '../../core/errors/failures.dart';
import '../../domain/entities/analisis_avanzado.dart';
import '../../domain/usecases/get_kelly_portafolio.dart';
import '../../domain/usecases/get_jugadores_partido.dart';
import '../../data/repositories/analisis_repo_impl.dart';

class AnalisisAvanzadoScreen extends StatefulWidget {
  final int partidoId;
  const AnalisisAvanzadoScreen({super.key, required this.partidoId});

  @override
  State<AnalisisAvanzadoScreen> createState() => _AnalisisAvanzadoScreenState();
}

class _AnalisisAvanzadoScreenState extends State<AnalisisAvanzadoScreen> {
  late final GetKellyPortafolio _getPortafolio;
  late final GetJugadoresPartido _getJugadores;

  KellyPortafolio? _portafolio;
  JugadoresPartido? _jugadores;
  bool _cargando = true;
  Failure? _errorPortafolio;
  Failure? _errorJugadores;

  @override
  void initState() {
    super.initState();
    final repo = AnalisisRepositoryImpl.create();
    _getPortafolio = GetKellyPortafolio(repo);
    _getJugadores = GetJugadoresPartido(repo);
    _cargar();
  }

  Future<void> _cargar() async {
    final futurePortafolio = _getPortafolio(widget.partidoId);
    final futureJugadores = _getJugadores(widget.partidoId);
    final rPortafolio = await futurePortafolio;
    final rJugadores = await futureJugadores;
    setState(() {
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
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Análisis avanzado', style: TextStyle(fontSize: 15)),
          bottom: TabBar(
            indicatorColor: c.pitch,
            labelColor: c.pitch,
            unselectedLabelColor: c.textSecond,
            tabs: const [
              Tab(text: 'KELLY PORTAFOLIO'),
              Tab(text: 'JUGADORES'),
            ],
          ),
        ),
        body: _cargando
            ? Center(child: CircularProgressIndicator(color: c.pitch))
            : TabBarView(
                children: [
                  _PortafolioTab(portafolio: _portafolio, error: _errorPortafolio),
                  _JugadoresTab(jugadores: _jugadores, error: _errorJugadores),
                ],
              ),
      ),
    );
  }
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
        for (final jug in jugadores)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(jug.nombre, style: TextStyle(color: c.text, fontWeight: FontWeight.w600)),
                      ),
                      if (jug.posicion != null)
                        Text(jug.posicion!, style: TextStyle(color: c.textSecond, fontSize: 12)),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 16,
                    runSpacing: 6,
                    children: [
                      _Chip('Tiros', jug.tirosPromedio.toStringAsFixed(1), c),
                      _Chip('Al arco', jug.tirosArcoPromedio.toStringAsFixed(1), c),
                      _Chip('Anota', '${(jug.probAnota * 100).toStringAsFixed(0)}%', c),
                      _Chip('Amarilla', '${(jug.probAmarilla * 100).toStringAsFixed(0)}%', c),
                      if (jug.probRoja > 0.01)
                        _Chip('Roja', '${(jug.probRoja * 100).toStringAsFixed(0)}%', c),
                    ],
                  ),
                ],
              ),
            ),
          ),
      ],
    );
  }
}

class _Chip extends StatelessWidget {
  final String label;
  final String valor;
  final AppColors c;
  const _Chip(this.label, this.valor, this.c);

  @override
  Widget build(BuildContext context) {
    return Text('$label: $valor', style: TextStyle(color: c.ledger, fontSize: 12));
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
