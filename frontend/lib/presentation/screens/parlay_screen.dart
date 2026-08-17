import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme.dart';
import '../../core/product_analytics.dart';
import '../../core/errors/failures.dart';
import '../../core/http/auth_client.dart';
import '../../domain/entities/parlay.dart';
import '../../domain/entities/partido.dart';
import '../../domain/usecases/get_kelly_mercados.dart';
import '../../data/repositories/analisis_repo_impl.dart';
import '../../data/datasources/parlay_remote_ds.dart';
import '../providers/partidos_provider.dart';
import '../providers/prediction_coupon_provider.dart';
import '../widgets/clay.dart';
import '../widgets/team_logo.dart';
import '../widgets/design_system.dart';
import '../widgets/app_bottom_nav.dart';

// Parlay entre partidos DISTINTOS, solo mercado 1X2 por pata — cualquier
// otro mercado (O/U, BTTS, hándicap...) existe en el backend pero armar
// un selector genérico para todos es mucho más superficie de la que
// pide un v1; 1X2 cubre el caso de uso más común de una combinada.
class _MercadoOpcion {
  final String clave;
  final String nombre;
  final double probabilidad;
  final double? cuota;
  final bool esJugador;
  const _MercadoOpcion(this.clave, this.nombre, this.probabilidad,
      {this.cuota, this.esJugador = false});
}

class ParlayScreen extends StatefulWidget {
  const ParlayScreen({super.key});

  @override
  State<ParlayScreen> createState() => _ParlayScreenState();
}

class _ParlayScreenState extends State<ParlayScreen> {
  bool _calculando = false;
  ParlayResultado? _resultado;
  String? _error;
  final Map<int, List<_MercadoOpcion>> _mercados = {};
  final Set<int> _cargandoMercados = {};

  @override
  void initState() {
    super.initState();
    ProductAnalytics.track('screen_view', {'screen': 'constructor_portafolio'});
    final provider = context.read<PartidosProvider>();
    if (provider.partidos.isEmpty) provider.cargarPartidosHoy();
  }

  void _toggle(Partido partido, _MercadoOpcion mercado, double? cuota) {
    final coupon = context.read<PredictionCouponProvider>();
    setState(() {
      coupon.toggle(CouponSelection(
        input: ParlaySeleccionInput(
            partidoId: partido.id, mercado: mercado.clave, cuota: cuota),
        partido: '${partido.local} vs ${partido.visitante}',
        liga: partido.liga,
        mercado: mercado.nombre,
        probabilidad: mercado.probabilidad,
      ));
      _resultado = null;
      _error = null;
    });
  }

  Future<void> _cargarMercados(int partidoId) async {
    if (_mercados.containsKey(partidoId) ||
        _cargandoMercados.contains(partidoId)) {
      return;
    }
    setState(() => _cargandoMercados.add(partidoId));
    final repo = AnalisisRepositoryImpl.create();
    final r = await GetKellyMercados(repo)(partidoId);
    final jugadores = await repo.getJugadores(partidoId);
    if (!mounted) return;
    setState(() {
      _cargandoMercados.remove(partidoId);
      _mercados[partidoId] = [
        ...?r.kelly?.todosMercados.where((m) => !m.sinCuota && m.cuota > 1).map(
            (m) => _MercadoOpcion(m.clave, m.mercado, m.probabilidad,
                cuota: m.cuota)),
        ...?jugadores.jugadores?.mercados.map((m) => _MercadoOpcion(
            m.clave, m.mercado, m.probabilidad,
            esJugador: true)),
      ];
      if (r.error != null) _error = r.error!.mensaje;
    });
  }

  Future<void> _elegirMercado(Partido partido, _MercadoOpcion mercado) async {
    double? cuota = mercado.cuota;
    if (mercado.esJugador) {
      final controller = TextEditingController();
      cuota = await showDialog<double>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Ingresa la cuota'),
          content: Column(mainAxisSize: MainAxisSize.min, children: [
            Text(mercado.nombre),
            const SizedBox(height: 12),
            TextField(
              controller: controller,
              autofocus: true,
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(
                  labelText: 'Cuota decimal de Betano u otra casa',
                  hintText: 'Ej. 1.85'),
            ),
          ]),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Cancelar')),
            FilledButton(
              onPressed: () {
                final valor =
                    double.tryParse(controller.text.replaceAll(',', '.'));
                if (valor != null && valor > 1) Navigator.pop(context, valor);
              },
              child: const Text('Agregar'),
            ),
          ],
        ),
      );
      controller.dispose();
      if (cuota == null) return;
    }
    _toggle(partido, mercado, cuota);
  }

  Future<void> _calcular() async {
    setState(() {
      _calculando = true;
      _error = null;
    });
    try {
      final ds = ParlayRemoteDataSource(AuthClient());
      final selecciones = context
          .read<PredictionCouponProvider>()
          .items
          .map((item) => item.input)
          .toList();
      final resultado = await ds.calcular(selecciones);
      if (resultado.parlayId != null) {
        ProductAnalytics.track('selection_saved', {'type': 'combinada'});
      }
      setState(() => _resultado = resultado);
    } on Failure catch (f) {
      setState(() => _error = f.mensaje);
    } catch (e) {
      setState(() => _error = 'Sin conexión: $e');
    } finally {
      setState(() => _calculando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final coupon = context.watch<PredictionCouponProvider>();
    return Scaffold(
      appBar: const AppHeader(
          showBack: true,
          title: 'Construir portafolio',
          subtitle: 'Combina selecciones y mide la exposición'),
      body: Consumer<PartidosProvider>(
        builder: (context, provider, _) {
          final conPrediccion =
              provider.partidos.where((p) => p.tienePred).toList();
          if (provider.cargando) {
            return Center(child: CircularProgressIndicator(color: c.pitch));
          }
          if (conPrediccion.isEmpty) {
            return Center(
                child: Text('Sin partidos con predicción hoy',
                    style: TextStyle(color: c.textSecond)));
          }
          return Column(children: [
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: conPrediccion.length,
                itemBuilder: (_, i) => _MatchPicker(
                  partido: conPrediccion[i],
                  seleccionado: coupon.forMatch(conPrediccion[i].id)?.input.mercado,
                  onPick: (mercado) =>
                      _elegirMercado(conPrediccion[i], mercado),
                  mercados: _mercados[conPrediccion[i].id],
                  cargando: _cargandoMercados.contains(conPrediccion[i].id),
                  onExpand: () => _cargarMercados(conPrediccion[i].id),
                ),
              ),
            ),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Text(_error!,
                    style: TextStyle(color: c.brick, fontSize: 12.5),
                    textAlign: TextAlign.center),
              ),
            if (_resultado != null)
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
                child: _ResultadoCard(resultado: _resultado!),
              ),
            Padding(
              padding: const EdgeInsets.all(16),
              child: ClayButton(
                label: coupon.count < 2
                    ? 'Selecciona 2+ partidos (${coupon.count}/2)'
                    : 'Calcular combinada (${coupon.count} patas)',
                loading: _calculando,
                onPressed: coupon.count < 2 ? null : _calcular,
              ),
            ),
          ]);
        },
      ),
      bottomNavigationBar: const AppBottomNav(current: AppTab.portafolio),
    );
  }
}

class _MatchPicker extends StatelessWidget {
  final Partido partido;
  final String? seleccionado;
  final ValueChanged<_MercadoOpcion> onPick;
  final List<_MercadoOpcion>? mercados;
  final bool cargando;
  final VoidCallback onExpand;
  const _MatchPicker(
      {required this.partido,
      required this.seleccionado,
      required this.onPick,
      required this.mercados,
      required this.cargando,
      required this.onExpand});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: seleccionado != null ? c.pitchSoft : c.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: seleccionado != null ? c.pitch : c.line),
      ),
      child: ExpansionTile(
        tilePadding: EdgeInsets.zero,
        childrenPadding: const EdgeInsets.only(top: 8),
        onExpansionChanged: (open) {
          if (open) onExpand();
        },
        title: Row(children: [
          TeamLogo(url: partido.localLogo, nombre: partido.local, size: 18),
          const SizedBox(width: 5),
          Flexible(
            child: Text('${partido.local} vs ${partido.visitante}',
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                    fontSize: 13.5,
                    fontWeight: FontWeight.w600,
                    color: c.text)),
          ),
          const SizedBox(width: 5),
          TeamLogo(
              url: partido.visitanteLogo, nombre: partido.visitante, size: 18),
        ]),
        subtitle: Text(
          seleccionado == null ? partido.liga : '1 mercado seleccionado',
          style: TextStyle(fontSize: 11, color: c.textSecond),
        ),
        children: [
          if (cargando)
            const Padding(
                padding: EdgeInsets.all(16),
                child: CircularProgressIndicator()),
          if (!cargando && mercados != null && mercados!.isEmpty)
            Padding(
                padding: const EdgeInsets.all(12),
                child: Text('Sin mercados con cuota disponible',
                    style: TextStyle(color: c.textSecond))),
          if (mercados != null)
            for (final m in mercados!) _opcion(m, c),
        ],
      ),
    );
  }

  Widget _opcion(_MercadoOpcion mercado, AppColors c) {
    final activo = seleccionado == mercado.clave;
    return Padding(
      padding: const EdgeInsets.only(bottom: 7),
      child: InkWell(
        onTap: () => onPick(mercado),
        borderRadius: BorderRadius.circular(10),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 10),
          decoration: BoxDecoration(
            color: activo ? c.pitch : c.bg2,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Row(children: [
            if (mercado.esJugador) ...[
              Icon(Icons.person_rounded,
                  size: 15, color: activo ? c.bg : c.ledger),
              const SizedBox(width: 7),
            ],
            Expanded(
                child: Text(mercado.nombre,
                    style: TextStyle(
                        color: activo ? c.bg : c.text,
                        fontWeight: FontWeight.w600))),
            Text('${(mercado.probabilidad * 100).toStringAsFixed(0)}%',
                style: TextStyle(color: activo ? c.bg : c.textSecond)),
            const SizedBox(width: 10),
            Text(mercado.cuota?.toStringAsFixed(2) ?? 'Ingresar cuota',
                style: AppTheme.score(c, size: 12)
                    .copyWith(color: activo ? c.bg : c.pitch)),
          ]),
        ),
      ),
    );
  }
}

class _ResultadoCard extends StatelessWidget {
  final ParlayResultado resultado;
  const _ResultadoCard({required this.resultado});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return ClayContainer(
      child: Column(children: [
        Row(mainAxisAlignment: MainAxisAlignment.spaceAround, children: [
          _metric(
              'Cuota', resultado.cuotaCombinada.toStringAsFixed(2), c.text, c),
          _metric(
              'Prob',
              '${(resultado.probCombinada * 100).toStringAsFixed(1)}%',
              c.text,
              c),
          _metric('Stake', '${resultado.stakePct.toStringAsFixed(1)}%',
              resultado.esValueBet ? c.pitch : c.textSecond, c),
          _metric('EV', '${(resultado.ev * 100).toStringAsFixed(1)}%',
              resultado.esValueBet ? c.pitch : c.brick, c),
        ]),
        if (!resultado.esValueBet) ...[
          const SizedBox(height: 8),
          Text('Sin valor — el modelo no recomienda esta combinada',
              style: TextStyle(fontSize: 11.5, color: c.textSecond),
              textAlign: TextAlign.center),
        ],
      ]),
    );
  }

  Widget _metric(String label, String valor, Color color, AppColors c) {
    return Column(children: [
      Text(valor, style: AppTheme.score(c, size: 15).copyWith(color: color)),
      const SizedBox(height: 2),
      Text(label, style: TextStyle(fontSize: 10.5, color: c.textSecond)),
    ]);
  }
}
