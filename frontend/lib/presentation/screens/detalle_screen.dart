import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme.dart';
import '../../core/constants.dart';
import '../../domain/usecases/get_detalle_partido.dart';
import '../../data/repositories/partido_repo_impl.dart';
import '../../domain/entities/partido.dart';
import '../../domain/entities/prediccion.dart';
import '../widgets/clay.dart';
import '../widgets/confidence.dart';

class DetalleScreen extends StatefulWidget {
  final int partidoId;
  const DetalleScreen({super.key, required this.partidoId});

  @override
  State<DetalleScreen> createState() => _DetalleScreenState();
}

class _DetalleScreenState extends State<DetalleScreen> {
  late final GetDetallePartido _getDetalle;
  Partido? _partido;
  bool _cargando = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _getDetalle = GetDetallePartido(PartidoRepositoryImpl.create());
    _cargar();
  }

  Future<void> _cargar() async {
    final result = await _getDetalle(widget.partidoId);
    setState(() {
      _partido = result.partido;
      _error = result.error?.mensaje;
      _cargando = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: Icon(Icons.arrow_back_ios_new_rounded, color: c.textSecond, size: 18),
          onPressed: () => context.go('/'),
        ),
        title: Text(
          _partido != null ? '${_partido!.local} vs ${_partido!.visitante}' : 'Detalle partido',
          style: const TextStyle(fontSize: 14),
          overflow: TextOverflow.ellipsis,
        ),
      ),
      body: _cargando
          ? Center(child: CircularProgressIndicator(color: c.pitch))
          : _error != null
              ? Center(child: Text(_error!, style: TextStyle(color: c.brick)))
              : _Contenido(partido: _partido!),
    );
  }
}

class _Contenido extends StatelessWidget {
  final Partido partido;
  const _Contenido({required this.partido});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final pred = partido.prediccion;
    return SingleChildScrollView(
      padding: const EdgeInsets.only(bottom: 24),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        _Header(partido: partido),
        if (pred != null) ...[
          Center(
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: ConfidenceDial(
                value: pred.confianza,
                label: pred.resultado == 'Empate' ? 'EMPATE' : 'GANA ${pred.resultado.toUpperCase()}',
              ),
            ),
          ),
          if (pred.mercados.isNotEmpty) _Seccion(
            titulo: 'Mercados recomendados',
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Wrap(
                spacing: 8, runSpacing: 8,
                children: pred.mercados.map((m) => _MarketChip(mercado: m)).toList(),
              ),
            ),
          ),
          if (pred.factores.isNotEmpty || pred.resumenH2h != null) _Seccion(
            titulo: 'Por qué',
            child: _Factores(pred: pred),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
            child: ClayButton(
              label: 'Kelly portafolio y jugadores',
              icon: Icons.insights_rounded,
              onPressed: () => context.go('/partido/${partido.id}/avanzado'),
            ),
          ),
        ] else
          Padding(
            padding: const EdgeInsets.all(24),
            child: Text('Sin predicción disponible — falta historial suficiente.',
                style: TextStyle(color: c.textSecond), textAlign: TextAlign.center),
          ),
      ]),
    );
  }
}

class _Header extends StatelessWidget {
  final Partido partido;
  const _Header({required this.partido});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 6, 20, 18),
      child: Column(children: [
        Text(partido.liga.toUpperCase(), style: AppTheme.eyebrow(c, color: c.ledger)),
        const SizedBox(height: 14),
        Row(mainAxisAlignment: MainAxisAlignment.center, children: [
          Expanded(child: Text(partido.local, textAlign: TextAlign.right,
              style: TextStyle(fontSize: 14.5, fontWeight: FontWeight.w600, color: c.text))),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Text(partido.marcador, style: AppTheme.score(c, size: 22)),
          ),
          Expanded(child: Text(partido.visitante,
              style: TextStyle(fontSize: 14.5, fontWeight: FontWeight.w600, color: c.text))),
        ]),
        const SizedBox(height: 10),
        Text(partido.jornada ?? partido.hora, style: TextStyle(fontSize: 11, color: c.textMuted)),
      ]),
    );
  }
}

class _Seccion extends StatelessWidget {
  final String titulo;
  final Widget child;
  const _Seccion({required this.titulo, required this.child});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const SizedBox(height: 6),
      Padding(
        padding: const EdgeInsets.fromLTRB(16, 0, 16, 10),
        child: Text(titulo.toUpperCase(), style: AppTheme.eyebrow(c)),
      ),
      child,
      const SizedBox(height: 6),
    ]);
  }
}

class _MarketChip extends StatelessWidget {
  final Mercado mercado;
  const _MarketChip({required this.mercado});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final recomendado = mercado.probabilidad >= AppConstants.umbralMercado;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: recomendado ? c.ledgerSoft : Colors.transparent,
        borderRadius: BorderRadius.circular(11),
        border: Border.all(color: recomendado ? c.ledger : c.lineStrong, width: recomendado ? 1 : 0.7),
      ),
      child: Text('${mercado.mercado} · ${(mercado.probabilidad * 100).toStringAsFixed(0)}%',
          style: TextStyle(
              fontSize: 11.5,
              color: recomendado ? c.ledger : c.textSecond,
              fontWeight: recomendado ? FontWeight.w600 : FontWeight.normal)),
    );
  }
}

class _Factores extends StatelessWidget {
  final Prediccion pred;
  const _Factores({required this.pred});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(children: [
        for (final f in pred.factores) _FactorRow(factor: f),
        if (pred.resumenH2h != null)
          Padding(
            padding: const EdgeInsets.only(top: 10),
            child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Container(
                width: 30, height: 30,
                decoration: BoxDecoration(color: c.bg2, borderRadius: BorderRadius.circular(9)),
                alignment: Alignment.center,
                child: Text('H2H', style: AppTheme.score(c, size: 8.5).copyWith(color: c.textSecond)),
              ),
              const SizedBox(width: 11),
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Text(pred.resumenH2h!, style: TextStyle(fontSize: 12, color: c.textSecond, height: 1.35)),
                ),
              ),
            ]),
          ),
      ]),
    );
  }
}

class _FactorRow extends StatelessWidget {
  final Factor factor;
  const _FactorRow({required this.factor});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final Color bg;
    final Color fg;
    final String pill;
    final Border? border;
    switch (factor.favorece) {
      case 'local':
        bg = c.pitchSoft; fg = c.pitch; pill = 'L'; border = null;
        break;
      case 'visitante':
        bg = Colors.transparent; fg = c.pitch; pill = 'V'; border = Border.all(color: c.pitch, width: 1.3);
        break;
      default:
        bg = c.bg2; fg = c.textMuted; pill = '='; border = null;
    }
    return Container(
      decoration: BoxDecoration(border: Border(bottom: BorderSide(color: c.line))),
      padding: const EdgeInsets.symmetric(vertical: 10),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Container(
          width: 28, height: 28,
          decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(9), border: border),
          alignment: Alignment.center,
          child: Text(pill, style: AppTheme.score(c, size: 10).copyWith(color: fg)),
        ),
        const SizedBox(width: 11),
        Expanded(
          child: Padding(
            padding: const EdgeInsets.only(top: 5),
            child: Text(factor.texto, style: TextStyle(fontSize: 12, color: c.textSecond, height: 1.35)),
          ),
        ),
      ]),
    );
  }
}
