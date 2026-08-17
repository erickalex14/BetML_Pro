import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../core/theme.dart';
import '../providers/prediction_coupon_provider.dart';

class PredictionCouponBubble extends StatelessWidget {
  const PredictionCouponBubble({super.key});

  @override
  Widget build(BuildContext context) {
    final coupon = Provider.of<PredictionCouponProvider?>(context);
    if (coupon == null || coupon.isEmpty) return const SizedBox.shrink();
    return Semantics(
        button: true,
        label: 'Abrir cupón con ${coupon.count} selecciones',
        child: FloatingActionButton.small(
          heroTag: 'prediction-coupon',
          tooltip: 'Abrir cupón',
          backgroundColor: context.colors.pitch,
          foregroundColor: Colors.white,
          onPressed: () => _openCoupon(context),
          child: Stack(clipBehavior: Clip.none, children: [
            const Icon(Icons.receipt_long_rounded),
            Positioned(
              right: -9,
              top: -9,
              child: CircleAvatar(
                radius: 9,
                backgroundColor: context.colors.pitch,
                child: Text('${coupon.count}',
                    style: const TextStyle(fontSize: 10, color: Colors.white)),
              ),
            ),
          ]),
        ),
      );
  }
}

void _openCoupon(BuildContext context) {
  showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    builder: (_) => const _CouponSheet(),
  );
}

class _CouponSheet extends StatelessWidget {
  const _CouponSheet();

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final coupon = context.watch<PredictionCouponProvider>();
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Row(children: [
            Expanded(
              child: Text('Cupón de predicciones  ${coupon.count}/30',
                  style: const TextStyle(fontWeight: FontWeight.w700)),
            ),
            IconButton(
              tooltip: 'Vaciar cupón',
              onPressed: coupon.clear,
              icon: const Icon(Icons.delete_outline_rounded),
            ),
            IconButton(
              tooltip: 'Compartir',
              onPressed: () async {
                final text = coupon.items
                    .map((i) => '${i.partido}: ${i.mercado}')
                    .join('\n');
                await Clipboard.setData(ClipboardData(text: text));
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Cupón copiado')));
                }
              },
              icon: const Icon(Icons.ios_share_rounded),
            ),
          ]),
          Flexible(
            child: ListView.separated(
              shrinkWrap: true,
              itemCount: coupon.count,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (_, index) {
                final item = coupon.items[index];
                return Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: c.surface,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: c.line),
                  ),
                  child: Row(children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(item.partido,
                              style: const TextStyle(fontWeight: FontWeight.w700)),
                          const SizedBox(height: 3),
                          Text(item.mercado,
                              style: TextStyle(color: c.textSecond, fontSize: 12)),
                          const SizedBox(height: 5),
                          Text('${(item.probabilidad * 100).toStringAsFixed(0)}% del modelo',
                              style: TextStyle(color: c.pitch, fontSize: 12,
                                  fontWeight: FontWeight.w600)),
                        ],
                      ),
                    ),
                    IconButton(
                      tooltip: 'Quitar selección',
                      onPressed: () => coupon.remove(item.input.partidoId),
                      icon: const Icon(Icons.delete_outline_rounded),
                    ),
                  ]),
                );
              },
            ),
          ),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              onPressed: coupon.count < 2
                  ? null
                  : () {
                      Navigator.pop(context);
                      context.push('/parlay');
                    },
              icon: const Icon(Icons.analytics_outlined),
              label: Text(coupon.count < 2
                  ? 'Agrega otra selección para analizar'
                  : 'Analizar cupón'),
            ),
          ),
        ]),
      ),
    );
  }
}
