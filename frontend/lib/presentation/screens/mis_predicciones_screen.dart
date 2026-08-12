import 'package:flutter/material.dart';
import '../../core/theme.dart';
import '../../domain/entities/prediccion.dart';
import '../../domain/usecases/get_predicciones_mias.dart';
import '../../data/repositories/partido_repo_impl.dart';
import '../widgets/app_bottom_nav.dart';

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
        : _todas.where((p) => switch (_filtro) {
              'pendiente' => p.pendiente,
              'acertada' => p.acerto == true,
              'fallada' => p.acerto == false,
              _ => true,
            }).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Mis predicciones'),
        actions: [IconButton(icon: Icon(Icons.refresh, color: c.textSecond), onPressed: _cargar)],
      ),
      body: _cargando
          ? Center(child: CircularProgressIndicator(color: c.pitch))
          : _error != null
              ? Center(child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text(_error!, style: TextStyle(color: c.brick), textAlign: TextAlign.center)))
              : Column(children: [
                  _ResumenBar(todas: _todas),
                  _FiltroChips(actual: _filtro, onChange: (f) => setState(() => _filtro = f)),
                  Expanded(
                    child: visibles.isEmpty
                        ? Center(child: Text('Sin predicciones acá', style: TextStyle(color: c.textSecond)))
                        : ListView.builder(
                            padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
                            itemCount: visibles.length,
                            itemBuilder: (_, i) => _PrediccionRow(p: visibles[i]),
                          ),
                  ),
                ]),
      bottomNavigationBar: const AppBottomNav(current: AppTab.predicciones),
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
        _stat('Accuracy', accuracy != null ? '${(accuracy * 100).toStringAsFixed(0)}%' : '—', c.text, c),
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
      (null, 'Todas'), ('pendiente', 'Pendientes'), ('acertada', 'Acertadas'), ('fallada', 'Falladas'),
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
                  border: Border.all(color: selected ? c.pitch : c.lineStrong, width: 0.7),
                ),
                child: Text(o.$2, style: TextStyle(color: selected ? c.bg : c.textSecond, fontSize: 12)),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}

class _PrediccionRow extends StatelessWidget {
  final PrediccionGuardada p;
  const _PrediccionRow({required this.p});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final Color estadoColor;
    final String estadoTexto;
    if (p.pendiente) {
      estadoColor = c.ledger; estadoTexto = 'Pendiente';
    } else if (p.acerto == true) {
      estadoColor = c.pitch; estadoTexto = 'Acertó';
    } else {
      estadoColor = c.brick; estadoTexto = 'Falló';
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(13),
      decoration: BoxDecoration(
        color: c.surface,
        borderRadius: BorderRadius.circular(13),
        border: Border.all(color: c.line),
      ),
      child: Row(children: [
        Container(width: 3, height: 34, decoration: BoxDecoration(color: estadoColor, borderRadius: BorderRadius.circular(2))),
        const SizedBox(width: 11),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            if (p.local != null)
              Text('${p.local} vs ${p.visitante}', style: TextStyle(fontSize: 12.5, fontWeight: FontWeight.w600, color: c.text)),
            const SizedBox(height: 2),
            Text('${p.prediccion} · ${(p.probabilidad * 100).toStringAsFixed(0)}%',
                style: TextStyle(fontSize: 11.5, color: c.textSecond)),
          ]),
        ),
        Text(estadoTexto, style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.w600, color: estadoColor)),
      ]),
    );
  }
}
