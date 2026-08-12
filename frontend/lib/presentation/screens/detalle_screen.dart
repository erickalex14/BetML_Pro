import 'dart:async';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme.dart';
import '../../core/constants.dart';
import '../../domain/usecases/get_detalle_partido.dart';
import '../../domain/usecases/get_prediccion_en_vivo.dart';
import '../../data/repositories/partido_repo_impl.dart';
import '../../domain/entities/partido.dart';
import '../../domain/entities/prediccion.dart';
import '../widgets/clay.dart';
import '../widgets/confidence.dart';
import '../widgets/team_logo.dart';

class DetalleScreen extends StatefulWidget {
  final int partidoId;
  const DetalleScreen({super.key, required this.partidoId});

  @override
  State<DetalleScreen> createState() => _DetalleScreenState();
}

class _DetalleScreenState extends State<DetalleScreen> {
  late final GetDetallePartido _getDetalle;
  late final GetPrediccionEnVivo _getPrediccionEnVivo;
  Partido? _partido;
  PrediccionEnVivo? _prediccionEnVivo;
  bool _cargando = true;
  String? _error;
  Timer? _autoRefresh;

  @override
  void initState() {
    super.initState();
    final repo = PartidoRepositoryImpl.create();
    _getDetalle = GetDetallePartido(repo);
    _getPrediccionEnVivo = GetPrediccionEnVivo(repo);
    _cargar();
  }

  @override
  void dispose() {
    _autoRefresh?.cancel();
    super.dispose();
  }

  Future<void> _cargar() async {
    final result = await _getDetalle(widget.partidoId);
    if (!mounted) return;
    setState(() {
      _partido = result.partido;
      _error = result.error?.mensaje;
      _cargando = false;
    });
    // Solo pollea mientras el partido está en juego — antes/después no
    // hay nada que vaya a cambiar entre refrescos.
    _autoRefresh?.cancel();
    if (_partido != null && _partido!.enJuego) {
      final enVivo = await _getPrediccionEnVivo(widget.partidoId);
      if (!mounted) return;
      setState(() => _prediccionEnVivo = enVivo.prediccion);
      _autoRefresh = Timer(const Duration(seconds: 60), _cargar);
    } else {
      _prediccionEnVivo = null;
    }
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
              : _Contenido(partido: _partido!, prediccionEnVivo: _prediccionEnVivo),
    );
  }
}

class _Contenido extends StatelessWidget {
  final Partido partido;
  final PrediccionEnVivo? prediccionEnVivo;
  const _Contenido({required this.partido, this.prediccionEnVivo});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final pred = partido.prediccion;
    return SingleChildScrollView(
      padding: const EdgeInsets.only(bottom: 24),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        _Header(partido: partido),
        if (partido.enJuego && prediccionEnVivo != null) _Seccion(
          titulo: 'Probabilidad en vivo',
          child: _ProbabilidadEnVivo(pred: prediccionEnVivo!),
        ),
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
          Expanded(
            child: Column(children: [
              TeamLogo(url: partido.localLogo, nombre: partido.local, size: 40),
              const SizedBox(height: 8),
              Text(partido.local, textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 14.5, fontWeight: FontWeight.w600, color: c.text)),
            ]),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Column(children: [
              Text(partido.marcador, style: AppTheme.score(c, size: 22)),
              if (partido.enJuego) ...[
                const SizedBox(height: 4),
                Row(mainAxisSize: MainAxisSize.min, children: [
                  Container(width: 6, height: 6, decoration: BoxDecoration(color: c.brick, shape: BoxShape.circle)),
                  const SizedBox(width: 4),
                  Text(partido.minutoTexto, style: TextStyle(fontSize: 11, color: c.brick, fontWeight: FontWeight.w700)),
                ]),
              ],
            ]),
          ),
          Expanded(
            child: Column(children: [
              TeamLogo(url: partido.visitanteLogo, nombre: partido.visitante, size: 40),
              const SizedBox(height: 8),
              Text(partido.visitante, textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 14.5, fontWeight: FontWeight.w600, color: c.text)),
            ]),
          ),
        ]),
        const SizedBox(height: 10),
        Text(partido.fechaHoraLarga, style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.w600, color: c.textSecond)),
        if (partido.jornada != null) ...[
          const SizedBox(height: 2),
          Text(partido.jornada!, style: TextStyle(fontSize: 11, color: c.textMuted)),
        ],
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

class _ProbabilidadEnVivo extends StatelessWidget {
  final PrediccionEnVivo pred;
  const _ProbabilidadEnVivo({required this.pred});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    Widget prob(String label, double valor) => Expanded(
          child: Column(children: [
            Text('${(valor * 100).toStringAsFixed(0)}%', style: AppTheme.score(c, size: 18).copyWith(color: c.pitch)),
            const SizedBox(height: 2),
            Text(label, style: TextStyle(fontSize: 10.5, color: c.textSecond)),
          ]),
        );
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(color: c.surface, borderRadius: BorderRadius.circular(13), border: Border.all(color: c.line)),
        child: Column(children: [
          Row(children: [
            prob('Local', pred.probLocal),
            prob('Empate', pred.probEmpate),
            prob('Visitante', pred.probVisitante),
          ]),
          const SizedBox(height: 8),
          Text('Recalculado desde el marcador actual (${pred.marcadorActual}) — no la predicción pre-partido',
              style: TextStyle(fontSize: 10.5, color: c.textMuted), textAlign: TextAlign.center),
        ]),
      ),
    );
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
