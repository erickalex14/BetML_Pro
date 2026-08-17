import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme.dart';
import '../../core/product_analytics.dart';
import '../../domain/entities/prediccion.dart';
import '../../domain/usecases/get_predicciones_mias.dart';
import '../../data/repositories/partido_repo_impl.dart';
import '../widgets/app_bottom_nav.dart';
import '../widgets/team_logo.dart';
import '../widgets/design_system.dart';

class MisPrediccionesScreen extends StatefulWidget {
  const MisPrediccionesScreen({super.key});

  @override
  State<MisPrediccionesScreen> createState() => _MisPrediccionesScreenState();
}

class _MisPrediccionesScreenState extends State<MisPrediccionesScreen> {
  late final GetPrediccionesMias _getMias;
  List<PrediccionGuardada> _todas = [];
  bool _cargando = true;
  String? _error;
  String? _filtro; // null=todas, "pendiente", "acertada", "fallada"

  @override
  void initState() {
    super.initState();
    ProductAnalytics.track('screen_view', {'screen': 'portafolio'});
    _getMias = GetPrediccionesMias(PartidoRepositoryImpl.create());
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() => _cargando = true);
    final r = await _getMias();
    setState(() {
      _todas = r.predicciones;
      _error = r.error?.mensaje;
      _cargando = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final visibles = _filtro == null
        ? _todas
        : _todas
            .where((p) => switch (_filtro) {
                  'pendiente' => p.pendiente,
                  'acertada' => p.acerto == true,
                  'fallada' => p.acerto == false,
                  _ => true,
                })
            .toList();

    return Scaffold(
      appBar: AppHeader(
        title: 'Portafolio',
        subtitle: 'Selecciones guardadas y seguimiento',
        actions: [
          IconButton(
              icon: const Icon(Icons.add_chart_rounded),
              tooltip: 'Construir portafolio',
              onPressed: () => context.push('/parlay')),
          IconButton(
              icon: Icon(Icons.refresh, color: c.textSecond),
              onPressed: _cargar),
        ],
      ),
      body: _cargando
          ? Center(child: CircularProgressIndicator(color: c.pitch))
          : _error != null
              ? Center(
                  child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Text(_error!,
                          style: TextStyle(color: c.brick),
                          textAlign: TextAlign.center)))
              : Column(children: [
                  _ResumenBar(todas: _todas),
                  _FiltroChips(
                      actual: _filtro,
                      onChange: (f) {
                        ProductAnalytics.track(
                            'filter_applied', {'type': 'estado_portafolio'});
                        setState(() => _filtro = f);
                      }),
                  Expanded(
                    child: visibles.isEmpty
                        ? const AppStateView(
                            icon: Icons.bookmark_border_rounded,
                            title: 'Portafolio vacío',
                            message:
                                'Guarda una oportunidad desde el análisis de un partido para consultarla aquí.')
                        : Builder(builder: (_) {
                            final grupos =
                                PrediccionesDePartido.agrupar(visibles);
                            return ListView.builder(
                              padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
                              itemCount: grupos.length,
                              itemBuilder: (_, i) =>
                                  _GrupoPartido(grupo: grupos[i]),
                            );
                          }),
                  ),
                ]),
      bottomNavigationBar: const AppBottomNav(current: AppTab.portafolio),
    );
  }
}

class _ResumenBar extends StatelessWidget {
  final List<PrediccionGuardada> todas;
  const _ResumenBar({required this.todas});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final pendientes = todas.where((p) => p.pendiente).length;
    final acertadas = todas.where((p) => p.acerto == true).length;
    final falladas = todas.where((p) => p.acerto == false).length;
    final cerradas = acertadas + falladas;
    final accuracy = cerradas > 0 ? acertadas / cerradas : null;

    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
      child: Row(mainAxisAlignment: MainAxisAlignment.spaceAround, children: [
        _stat('Pendientes', '$pendientes', c.ledger, c),
        _stat('Acertadas', '$acertadas', c.pitch, c),
        _stat('Falladas', '$falladas', c.brick, c),
        _stat(
            'Accuracy',
            accuracy != null ? '${(accuracy * 100).toStringAsFixed(0)}%' : '—',
            c.text,
            c),
      ]),
    );
  }

  Widget _stat(String label, String valor, Color color, AppColors c) {
    return Column(children: [
      Text(valor, style: AppTheme.score(c, size: 17).copyWith(color: color)),
      const SizedBox(height: 2),
      Text(label, style: TextStyle(fontSize: 10.5, color: c.textSecond)),
    ]);
  }
}

class _FiltroChips extends StatelessWidget {
  final String? actual;
  final ValueChanged<String?> onChange;
  const _FiltroChips({required this.actual, required this.onChange});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final opciones = [
      (null, 'Todas'),
      ('pendiente', 'Pendientes'),
      ('acertada', 'Acertadas'),
      ('fallada', 'Falladas'),
    ];
    return SizedBox(
      height: 34,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        children: opciones.map((o) {
          final selected = actual == o.$1;
          return Padding(
            padding: const EdgeInsets.only(right: 6),
            child: GestureDetector(
              onTap: () => onChange(o.$1),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 13),
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: selected ? c.pitch : Colors.transparent,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                      color: selected ? c.pitch : c.lineStrong, width: 0.7),
                ),
                child: Text(o.$2,
                    style: TextStyle(
                        color: selected ? c.bg : c.textSecond, fontSize: 12)),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}

// Una tarjeta por PARTIDO, con sus mercados adentro — antes cada
// mercado era una tarjeta suelta y un partido con 4 predicciones
// repetía 4 veces los nombres de los equipos.
class _GrupoPartido extends StatelessWidget {
  final PrediccionesDePartido grupo;
  const _GrupoPartido({required this.grupo});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return InkWell(
      onTap: () => context.push('/partido/${grupo.partidoId}'),
      borderRadius: BorderRadius.circular(14),
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          color: c.surface,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: c.line),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(13, 12, 13, 10),
            child: Row(children: [
              SizedBox(
                width: 44,
                child: Stack(children: [
                  TeamLogo(
                      url: grupo.localLogo,
                      nombre: grupo.local ?? '?',
                      size: 22),
                  Positioned(
                    left: 14,
                    child: Container(
                      padding: const EdgeInsets.all(1.5),
                      decoration: BoxDecoration(
                          color: c.surface, shape: BoxShape.circle),
                      child: TeamLogo(
                          url: grupo.visitanteLogo,
                          nombre: grupo.visitante ?? '?',
                          size: 22),
                    ),
                  ),
                ]),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('${grupo.local ?? '?'} — ${grupo.visitante ?? '?'}',
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                              color: c.text)),
                      const SizedBox(height: 2),
                      Text(grupo.liga ?? '', style: AppTheme.eyebrow(c)),
                    ]),
              ),
              const SizedBox(width: 8),
              Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
                if (grupo.marcador.isNotEmpty)
                  Text(grupo.marcador,
                      style:
                          AppTheme.score(c, size: 13).copyWith(color: c.text)),
                if (grupo.enJuego) ...[
                  const SizedBox(height: 2),
                  Row(mainAxisSize: MainAxisSize.min, children: [
                    Container(
                        width: 5,
                        height: 5,
                        decoration: BoxDecoration(
                            color: c.brick, shape: BoxShape.circle)),
                    const SizedBox(width: 3),
                    Text('EN VIVO',
                        style: TextStyle(
                            fontSize: 8.5,
                            color: c.brick,
                            fontWeight: FontWeight.w700)),
                  ]),
                ],
              ]),
            ]),
          ),
          // Resumen del partido — solo si hay más de un mercado, si no
          // el detalle de abajo ya lo dice todo
          if (grupo.predicciones.length > 1)
            Padding(
              padding: const EdgeInsets.fromLTRB(13, 0, 13, 8),
              child: Row(children: [
                if (grupo.acertadas > 0)
                  _pill(c, '${grupo.acertadas} acertó', c.pitch),
                if (grupo.falladas > 0)
                  _pill(c, '${grupo.falladas} falló', c.brick),
                if (grupo.pendientes > 0)
                  _pill(c, '${grupo.pendientes} pendiente', c.ledger),
              ]),
            ),
          Divider(height: 1, color: c.line),
          Padding(
            padding: const EdgeInsets.fromLTRB(13, 6, 13, 10),
            child: Column(
              children: [for (final p in grupo.predicciones) _MercadoRow(p: p)],
            ),
          ),
        ]),
      ),
    );
  }

  Widget _pill(AppColors c, String texto, Color color) {
    return Padding(
      padding: const EdgeInsets.only(right: 6),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2.5),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.13),
          borderRadius: BorderRadius.circular(7),
        ),
        child: Text(texto,
            style: TextStyle(
                fontSize: 9.5, color: color, fontWeight: FontWeight.w600)),
      ),
    );
  }
}

class _MercadoRow extends StatelessWidget {
  final PrediccionGuardada p;
  const _MercadoRow({required this.p});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final Color estadoColor;
    final String estadoTexto;
    if (p.pendiente) {
      estadoColor = c.ledger;
      estadoTexto = 'Pendiente';
    } else if (p.acerto == true) {
      estadoColor = c.pitch;
      estadoTexto = 'Acertó';
    } else {
      estadoColor = c.brick;
      estadoTexto = 'Falló';
    }

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(children: [
        Container(
            width: 3,
            height: 22,
            decoration: BoxDecoration(
                color: estadoColor, borderRadius: BorderRadius.circular(2))),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
              '${p.prediccion} · ${(p.probabilidad * 100).toStringAsFixed(0)}%',
              style: TextStyle(fontSize: 12, color: c.textSecond)),
        ),
        Text(estadoTexto,
            style: TextStyle(
                fontSize: 11, fontWeight: FontWeight.w600, color: estadoColor)),
      ]),
    );
  }
}
