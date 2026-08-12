import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme.dart';
import '../../core/errors/failures.dart';
import '../../core/http/auth_client.dart';
import '../../domain/entities/parlay.dart';
import '../../domain/entities/partido.dart';
import '../../data/datasources/parlay_remote_ds.dart';
import '../providers/partidos_provider.dart';
import '../widgets/clay.dart';
import '../widgets/team_logo.dart';

// Parlay entre partidos DISTINTOS, solo mercado 1X2 por pata — cualquier
// otro mercado (O/U, BTTS, hándicap...) existe en el backend pero armar
// un selector genérico para todos es mucho más superficie de la que
// pide un v1; 1X2 cubre el caso de uso más común de una combinada.
class ParlayScreen extends StatefulWidget {
  const ParlayScreen({super.key});

  @override
  State<ParlayScreen> createState() => _ParlayScreenState();
}

class _ParlayScreenState extends State<ParlayScreen> {
  final Map<int, String> _seleccion = {}; // partidoId -> "local"|"empate"|"visitante"
  bool _calculando = false;
  ParlayResultado? _resultado;
  String? _error;

  @override
  void initState() {
    super.initState();
    final provider = context.read<PartidosProvider>();
    if (provider.partidos.isEmpty) provider.cargarPartidosHoy();
  }

  void _toggle(int partidoId, String mercado) {
    setState(() {
      if (_seleccion[partidoId] == mercado) {
        _seleccion.remove(partidoId);
      } else {
        _seleccion[partidoId] = mercado;
      }
      _resultado = null;
      _error = null;
    });
  }

  Future<void> _calcular() async {
    setState(() { _calculando = true; _error = null; });
    try {
      final ds = ParlayRemoteDataSource(AuthClient());
      final selecciones = _seleccion.entries
          .map((e) => ParlaySeleccionInput(partidoId: e.key, mercado: e.value))
          .toList();
      final resultado = await ds.calcular(selecciones);
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
    return Scaffold(
      appBar: AppBar(title: const Text('Armar combinada')),
      body: Consumer<PartidosProvider>(
        builder: (context, provider, _) {
          final conPrediccion = provider.partidos.where((p) => p.tienePred).toList();
          if (provider.cargando) return Center(child: CircularProgressIndicator(color: c.pitch));
          if (conPrediccion.isEmpty) {
            return Center(child: Text('Sin partidos con predicción hoy', style: TextStyle(color: c.textSecond)));
          }
          return Column(children: [
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: conPrediccion.length,
                itemBuilder: (_, i) => _MatchPicker(
                  partido: conPrediccion[i],
                  seleccionado: _seleccion[conPrediccion[i].id],
                  onPick: (mercado) => _toggle(conPrediccion[i].id, mercado),
                ),
              ),
            ),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Text(_error!, style: TextStyle(color: c.brick, fontSize: 12.5), textAlign: TextAlign.center),
              ),
            if (_resultado != null)
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
                child: _ResultadoCard(resultado: _resultado!),
              ),
            Padding(
              padding: const EdgeInsets.all(16),
              child: ClayButton(
                label: _seleccion.length < 2
                    ? 'Elegí 2+ partidos (${_seleccion.length}/2)'
                    : 'Calcular combinada (${_seleccion.length} patas)',
                loading: _calculando,
                onPressed: _seleccion.length < 2 ? null : _calcular,
              ),
            ),
          ]);
        },
      ),
    );
  }
}

class _MatchPicker extends StatelessWidget {
  final Partido partido;
  final String? seleccionado;
  final ValueChanged<String> onPick;
  const _MatchPicker({required this.partido, required this.seleccionado, required this.onPick});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final pred = partido.prediccion!;
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: seleccionado != null ? c.pitchSoft : c.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: seleccionado != null ? c.pitch : c.line),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          TeamLogo(url: partido.localLogo, nombre: partido.local, size: 18),
          const SizedBox(width: 5),
          Flexible(
            child: Text('${partido.local} vs ${partido.visitante}',
                overflow: TextOverflow.ellipsis,
                style: TextStyle(fontSize: 13.5, fontWeight: FontWeight.w600, color: c.text)),
          ),
          const SizedBox(width: 5),
          TeamLogo(url: partido.visitanteLogo, nombre: partido.visitante, size: 18),
        ]),
        const SizedBox(height: 3),
        Text(partido.liga, style: TextStyle(fontSize: 11, color: c.textSecond)),
        const SizedBox(height: 10),
        Row(children: [
          _opcion('local', 'Local', pred.probLocal, c),
          const SizedBox(width: 6),
          _opcion('empate', 'Empate', pred.probEmpate, c),
          const SizedBox(width: 6),
          _opcion('visitante', 'Visita', pred.probVisitante, c),
        ]),
      ]),
    );
  }

  Widget _opcion(String clave, String label, double prob, AppColors c) {
    final activo = seleccionado == clave;
    return Expanded(
      child: GestureDetector(
        onTap: () => onPick(clave),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 8),
          decoration: BoxDecoration(
            color: activo ? c.pitch : c.bg2,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Column(children: [
            Text('${(prob * 100).toStringAsFixed(0)}%',
                style: AppTheme.score(c, size: 13).copyWith(color: activo ? c.bg : c.text)),
            Text(label, style: TextStyle(fontSize: 9.5, color: activo ? c.bg.withValues(alpha: 0.8) : c.textSecond)),
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
          _metric('Cuota', resultado.cuotaCombinada.toStringAsFixed(2), c.text, c),
          _metric('Prob', '${(resultado.probCombinada * 100).toStringAsFixed(1)}%', c.text, c),
          _metric('Stake', '${resultado.stakePct.toStringAsFixed(1)}%',
              resultado.esValueBet ? c.pitch : c.textSecond, c),
          _metric('EV', '${(resultado.ev * 100).toStringAsFixed(1)}%',
              resultado.esValueBet ? c.pitch : c.brick, c),
        ]),
        if (!resultado.esValueBet) ...[
          const SizedBox(height: 8),
          Text('Sin valor — el modelo no recomienda esta combinada',
              style: TextStyle(fontSize: 11.5, color: c.textSecond), textAlign: TextAlign.center),
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
