import 'package:flutter/material.dart';
import '../../core/theme.dart';

// Claymorphism — reservado a 2 lugares por pantalla (card destacada +
// nav inferior / CTA principal). Todo lo demás usa Card plano o lista
// con regla — si esto se usara en cada elemento dejaría de leerse como
// acento y la app entera parecería "solo tarjetas flotantes".
class ClayContainer extends StatelessWidget {
  final Widget child;
  final EdgeInsets padding;
  final double radius;
  const ClayContainer({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(16),
    this.radius = 20,
  });

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Container(
      padding: padding,
      decoration: BoxDecoration(
        color: c.surfaceClay,
        borderRadius: BorderRadius.circular(radius),
        border: Border.all(color: c.line),
        boxShadow: clayShadow(c, strength: 0.35),
      ),
      child: child,
    );
  }
}

class ClayButton extends StatelessWidget {
  final String label;
  final IconData? icon;
  final VoidCallback? onPressed;
  final bool loading;
  const ClayButton(
      {super.key,
      required this.label,
      this.icon,
      this.onPressed,
      this.loading = false});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return SizedBox(
      width: double.infinity,
      child: Material(
        color: c.pitch,
        borderRadius: BorderRadius.circular(14),
        elevation: 0,
        child: InkWell(
          borderRadius: BorderRadius.circular(14),
          onTap: loading ? null : onPressed,
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 13),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(14),
              boxShadow: clayShadow(c, strength: 0.3),
            ),
            child: Center(
              child: loading
                  ? SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: c.bg))
                  : Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (icon != null) ...[
                          Icon(icon, size: 17, color: c.bg),
                          const SizedBox(width: 7)
                        ],
                        Text(label,
                            style: TextStyle(
                                color: c.bg,
                                fontSize: 13.5,
                                fontWeight: FontWeight.w600)),
                      ],
                    ),
            ),
          ),
        ),
      ),
    );
  }
}
