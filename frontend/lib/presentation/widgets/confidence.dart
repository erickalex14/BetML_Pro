import 'dart:math';
import 'package:flutter/material.dart';
import '../../core/theme.dart';

// Dial de confianza — reemplaza la barra de progreso genérica. Nativo
// (CircularProgressIndicator con stroke grueso + rotación), sin pintar
// un CustomPainter a mano para lo que el widget de Flutter ya resuelve.
class ConfidenceDial extends StatelessWidget {
  final double value; // 0..1
  final String label;
  final double size;
  const ConfidenceDial({super.key, required this.value, required this.label, this.size = 140});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return SizedBox(
      width: size, height: size,
      child: Stack(alignment: Alignment.center, children: [
        SizedBox(
          width: size, height: size,
          child: CircularProgressIndicator(
            value: 1, strokeWidth: 12, color: c.bg2, backgroundColor: c.bg2),
        ),
        Transform.rotate(
          angle: -pi / 2,
          child: SizedBox(
            width: size, height: size,
            child: CircularProgressIndicator(
              value: value, strokeWidth: 12, strokeCap: StrokeCap.round,
              color: c.pitch, backgroundColor: Colors.transparent),
          ),
        ),
        Column(mainAxisSize: MainAxisSize.min, children: [
          Text('${(value * 100).toStringAsFixed(0)}%', style: AppTheme.score(c, size: 26)),
          const SizedBox(height: 2),
          Text(label, style: AppTheme.eyebrow(c)),
        ]),
      ]),
    );
  }
}

// Meter de 5 muescas — usado en la card destacada, discreto en vez de
// una barra continua (misma idea que una escala de fuerza de señal).
class ConfidenceMeter extends StatelessWidget {
  final double value; // 0..1
  const ConfidenceMeter({super.key, required this.value});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final activas = (value * 5).round().clamp(0, 5);
    return Row(
      children: List.generate(5, (i) {
        return Expanded(
          child: Container(
            height: 6,
            margin: EdgeInsets.only(right: i == 4 ? 0 : 3),
            decoration: BoxDecoration(
              color: i < activas ? c.ledger : c.bg2,
              borderRadius: BorderRadius.circular(3),
            ),
          ),
        );
      }),
    );
  }
}
