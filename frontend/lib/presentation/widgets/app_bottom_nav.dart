import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'prediction_coupon.dart';

enum AppTab { hoy, oportunidades, portafolio, rendimiento }

class AppBottomNav extends StatelessWidget {
  final AppTab current;
  const AppBottomNav({super.key, required this.current});

  static const _destinos = <({
    AppTab tab,
    IconData icon,
    IconData selected,
    String label,
    String route
  })>[
    (
      tab: AppTab.hoy,
      icon: Icons.today_outlined,
      selected: Icons.today_rounded,
      label: 'Hoy',
      route: '/'
    ),
    (
      tab: AppTab.oportunidades,
      icon: Icons.radar_outlined,
      selected: Icons.radar_rounded,
      label: 'Oportunidades',
      route: '/oportunidades'
    ),
    (
      tab: AppTab.portafolio,
      icon: Icons.bookmark_border_rounded,
      selected: Icons.bookmark_rounded,
      label: 'Portafolio',
      route: '/portafolio'
    ),
    (
      tab: AppTab.rendimiento,
      icon: Icons.insights_outlined,
      selected: Icons.insights_rounded,
      label: 'Rendimiento',
      route: '/rendimiento'
    ),
  ];

  @override
  Widget build(BuildContext context) {
    final index = _destinos.indexWhere((d) => d.tab == current);
    return SizedBox(
      height: 126,
      child: Stack(children: [
        Positioned(
          left: 0,
          right: 0,
          bottom: 0,
          child: NavigationBar(
            selectedIndex: index,
            onDestinationSelected: (next) {
              if (next != index) context.go(_destinos[next].route);
            },
            destinations: [
              for (final d in _destinos)
                NavigationDestination(
                    icon: Icon(d.icon),
                    selectedIcon: Icon(d.selected),
                    label: d.label,
                    tooltip: d.label)
            ],
          ),
        ),
        const Positioned(
            right: 18, top: 4, child: PredictionCouponBubble()),
      ]),
    );
  }
}
