import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme.dart';
import '../../domain/usecases/get_detalle_partido.dart';
import '../../data/repositories/partido_repo_impl.dart';
import '../../domain/entities/partido.dart';

class DetalleScreen extends StatefulWidget {
  final int partidoId;
  const DetalleScreen({super.key, required this.partidoId});

  @override
  State<DetalleScreen> createState() => _DetalleScreenState();
}

class _DetalleScreenState extends State<DetalleScreen> {
  late final GetDetallePartido _getDetalle;
  Partido? _partido;
  bool     _cargando = true;
  String?  _error;

  @override
  void initState() {
    super.initState();
    _getDetalle = GetDetallePartido(PartidoRepositoryImpl.create());
    _cargar();
  }

  Future<void> _cargar() async {
    final result = await _getDetalle(widget.partidoId);
    setState(() {
      _partido  = result.partido;
      _error    = result.error?.mensaje;
      _cargando = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppTheme.textSecond),
          onPressed: () => context.go('/'),
        ),
        title: Text(
          _partido != null
            ? '${_partido!.local} vs ${_partido!.visitante}'
            : 'Detalle Partido',
          style: const TextStyle(fontSize: 15),
        ),
      ),
      body: _cargando
        ? const Center(
            child: CircularProgressIndicator(color: AppTheme.primary))
        : _error != null
          ? Center(child: Text(_error!,
              style: const TextStyle(color: AppTheme.red)))
          : _buildContent(),
    );
  }

  Widget _buildContent() {
    final p = _partido!;
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(children: [
                Text(p.liga,
                  style: const TextStyle(
                    color: AppTheme.primary, fontSize: 12)),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    Expanded(
                      child: Text(p.local,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          fontSize: 16, fontWeight: FontWeight.w600)),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16, vertical: 8),
                      decoration: BoxDecoration(
                        color: AppTheme.surface2,
                        borderRadius: BorderRadius.circular(8)),
                      child: Text(p.marcador,
                        style: const TextStyle(
                          fontSize: 18, fontWeight: FontWeight.w700)),
                    ),
                    Expanded(
                      child: Text(p.visitante,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          fontSize: 16, fontWeight: FontWeight.w600)),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(p.jornada ?? '',
                  style: const TextStyle(
                    color: AppTheme.textSecond, fontSize: 11)),
              ]),
            ),
          ),
          const SizedBox(height: 12),

          // Predicción ML
          if (p.tienePred) ...[
            const Text('ANÁLISIS ML',
              style: TextStyle(
                color: AppTheme.textSecond,
                fontSize: 11,
                fontWeight: FontWeight.w600,
                letterSpacing: 1)),
            const SizedBox(height: 8),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(children: [
                      _BigProb('Local',
                        p.prediccion!.probLocal,
                        p.prediccion!.resultado == 'Local'),
                      _BigProb('Empate',
                        p.prediccion!.probEmpate,
                        p.prediccion!.resultado == 'Empate'),
                      _BigProb('Visitante',
                        p.prediccion!.probVisitante,
                        p.prediccion!.resultado == 'Visitante'),
                    ]),
                    const SizedBox(height: 12),
                    Row(children: [
                      const Text('Confianza: ',
                        style: TextStyle(
                          color: AppTheme.textSecond, fontSize: 12)),
                      Expanded(
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(2),
                          child: LinearProgressIndicator(
                            value: p.prediccion!.confianza,
                            backgroundColor: AppTheme.surface2,
                            valueColor: const AlwaysStoppedAnimation(
                              AppTheme.primary),
                            minHeight: 4,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        '${(p.prediccion!.confianza * 100).toStringAsFixed(0)}%',
                        style: const TextStyle(
                          color: AppTheme.primary, fontSize: 12)),
                    ]),
                    if (p.prediccion!.mercadosTop.isNotEmpty) ...[
                      const SizedBox(height: 16),
                      const Text('MERCADOS RECOMENDADOS',
                        style: TextStyle(
                          color: AppTheme.textSecond,
                          fontSize: 10,
                          letterSpacing: 1)),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 6,
                        runSpacing: 6,
                        children: p.prediccion!.mercadosTop
                          .map((m) => Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 5),
                            decoration: BoxDecoration(
                              color: AppTheme.amber.withValues(alpha: 0.15),
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(
                                color: AppTheme.amber, width: 0.5)),
                            child: Text(m.label,
                              style: const TextStyle(
                                color: AppTheme.amber,
                                fontSize: 12,
                                fontWeight: FontWeight.w500)),
                          )).toList(),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _BigProb extends StatelessWidget {
  final String label;
  final double prob;
  final bool   highlight;
  const _BigProb(this.label, this.prob, this.highlight);

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(children: [
        Text('${(prob * 100).toStringAsFixed(1)}%',
          style: TextStyle(
            color: highlight ? AppTheme.primary : AppTheme.textPrimary,
            fontSize: 22,
            fontWeight: FontWeight.w700)),
        Text(label,
          style: const TextStyle(
            color: AppTheme.textSecond, fontSize: 12)),
      ]),
    );
  }
}

