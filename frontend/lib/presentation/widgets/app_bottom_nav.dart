import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme.dart';
import 'clay.dart';

enum AppTab { partidos, stats, perfil }

// Nav clay — el segundo (y último) lugar donde se usa el tratamiento
// claymorphism, para que siga leyéndose como acento y no como wallpaper.
class AppBottomNav extends StatelessWidget {
  final AppTab current;
  const AppBottomNav({super.key, required this.current});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 14),
      child: ClayContainer(
        radius: 22,
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 6),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            _item(context, AppTab.partidos, Icons.receipt_long_outlined, 'Partidos', '/'),
            _item(context, AppTab.stats, Icons.show_chart_rounded, 'Stats', '/stats'),
            _item(context, AppTab.perfil, Icons.person_outline_rounded, 'Perfil', '/perfil'),
          ],
        ),
      ),
    );
  }

  Widget _item(BuildContext context, AppTab tab, IconData icon, String label, String ruta) {
    final c = context.colors;
    final active = tab == current;
    return GestureDetector(
      onTap: active ? null : () => context.go(ruta),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
        decoration: BoxDecoration(
          color: active ? c.pitch : Colors.transparent,
          borderRadius: BorderRadius.circular(14),
        ),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Icon(icon, size: 19, color: active ? c.bg : c.textMuted),
          const SizedBox(height: 3),
          Text(label, style: TextStyle(fontSize: 9.5, color: active ? c.bg : c.textMuted)),
        ]),
      ),
    );
  }
}
