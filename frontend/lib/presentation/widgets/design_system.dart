import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme.dart';

/// Política de Atrás para los cuatro destinos principales.
///
/// Android no tiene una ruta anterior cuando una pestaña se abrió con
/// `go()`. En ese caso primero vuelve a Hoy; desde Hoy exige un segundo
/// gesto para salir, evitando cierres accidentales por navegación lateral.
class AppRootBackGuard extends StatefulWidget {
  final bool isHome;
  final Widget child;

  const AppRootBackGuard({
    super.key,
    required this.isHome,
    required this.child,
  });

  @override
  State<AppRootBackGuard> createState() => _AppRootBackGuardState();
}

class AppSecondaryBackGuard extends StatelessWidget {
  final Widget child;
  final String fallbackRoute;
  const AppSecondaryBackGuard({
    super.key,
    required this.child,
    this.fallbackRoute = '/',
  });

  @override
  Widget build(BuildContext context) => PopScope(
        canPop: context.canPop(),
        onPopInvokedWithResult: (didPop, _) {
          if (!didPop) context.go(fallbackRoute);
        },
        child: child,
      );
}

class _AppRootBackGuardState extends State<AppRootBackGuard> {
  DateTime? _ultimoIntento;

  void _onBack(bool didPop) {
    if (didPop) return;
    if (!widget.isHome) {
      context.go('/');
      return;
    }

    final ahora = DateTime.now();
    if (_ultimoIntento != null &&
        ahora.difference(_ultimoIntento!) < const Duration(seconds: 2)) {
      SystemNavigator.pop();
      return;
    }
    _ultimoIntento = ahora;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(const SnackBar(
        content: Text('Deslizá nuevamente para salir'),
        duration: Duration(seconds: 2),
      ));
  }

  @override
  Widget build(BuildContext context) => PopScope(
        canPop: false,
        onPopInvokedWithResult: (didPop, _) => _onBack(didPop),
        child: widget.child,
      );
}

class AppHeader extends StatelessWidget implements PreferredSizeWidget {
  final String title;
  final String? subtitle;
  final List<Widget> actions;
  final bool showBack;
  final String fallbackRoute;

  const AppHeader({
    super.key,
    required this.title,
    this.subtitle,
    this.actions = const [],
    this.showBack = false,
    this.fallbackRoute = '/',
  });

  @override
  Size get preferredSize => Size.fromHeight(subtitle == null ? 64 : 72);

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return AppBar(
      toolbarHeight: preferredSize.height,
      automaticallyImplyLeading: false,
      leading: showBack
          ? IconButton(
              tooltip: 'Volver',
              icon: const Icon(Icons.arrow_back_rounded),
              onPressed: () => context.canPop()
                  ? context.pop()
                  : context.go(fallbackRoute),
            )
          : null,
      titleSpacing: showBack ? 0 : 16,
      title: Row(children: [
        if (!showBack) ...[
          ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: Image.asset('assets/logos/logo_icon.png',
                  width: 32, height: 32)),
          const SizedBox(width: 10),
        ],
        Expanded(
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
              Text(title, overflow: TextOverflow.ellipsis),
              if (subtitle != null)
                Text(subtitle!,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                        color: c.textSecond,
                        fontSize: 11.5,
                        fontWeight: FontWeight.w500)),
            ])),
      ]),
      actions: [
        ...actions,
        if (!showBack)
          IconButton(
            tooltip: 'Perfil y ajustes',
            onPressed: () => context.push('/perfil'),
            icon: CircleAvatar(
                radius: 17,
                backgroundColor: c.pitchSoft,
                child: Icon(Icons.person_outline_rounded,
                    color: c.pitch, size: 20)),
          ),
        const SizedBox(width: 6),
      ],
    );
  }
}

class SectionHeading extends StatelessWidget {
  final String title;
  final String? subtitle;
  final Widget? trailing;
  const SectionHeading(this.title, {super.key, this.subtitle, this.trailing});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
      Expanded(
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(title, style: Theme.of(context).textTheme.titleLarge),
        if (subtitle != null) ...[
          const SizedBox(height: 3),
          Text(subtitle!, style: TextStyle(color: c.textSecond, fontSize: 12)),
        ],
      ])),
      if (trailing != null) trailing!,
    ]);
  }
}

class DataPill extends StatelessWidget {
  final String label;
  final Color? color;
  final IconData? icon;
  const DataPill(this.label, {super.key, this.color, this.icon});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final accent = color ?? c.textSecond;
    return Container(
      constraints: const BoxConstraints(minHeight: 28),
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
          color: accent.withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(8)),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        if (icon != null) ...[
          Icon(icon, size: 13, color: accent),
          const SizedBox(width: 5)
        ],
        Text(label,
            style: TextStyle(
                color: accent, fontSize: 10.5, fontWeight: FontWeight.w700)),
      ]),
    );
  }
}

class MetricTile extends StatelessWidget {
  final String label;
  final String value;
  final Color? color;
  const MetricTile(
      {super.key, required this.label, required this.value, this.color});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Expanded(
        child: Container(
      constraints: const BoxConstraints(minHeight: 68),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
          color: c.bg2,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: c.line)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(value,
            style:
                AppTheme.score(c, size: 16).copyWith(color: color ?? c.text)),
        const SizedBox(height: 5),
        Text(label, style: TextStyle(color: c.textMuted, fontSize: 10.5)),
      ]),
    ));
  }
}

class AppStateView extends StatelessWidget {
  final IconData icon;
  final String title;
  final String message;
  final String? action;
  final VoidCallback? onAction;
  const AppStateView(
      {super.key,
      required this.icon,
      required this.title,
      required this.message,
      this.action,
      this.onAction});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Center(
        child: Padding(
      padding: const EdgeInsets.all(32),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        Container(
            width: 52,
            height: 52,
            decoration: BoxDecoration(color: c.bg2, shape: BoxShape.circle),
            child: Icon(icon, color: c.textMuted, size: 26)),
        const SizedBox(height: 14),
        Text(title,
            style: Theme.of(context).textTheme.titleMedium,
            textAlign: TextAlign.center),
        const SizedBox(height: 6),
        Text(message,
            style: TextStyle(color: c.textSecond, fontSize: 12.5, height: 1.4),
            textAlign: TextAlign.center),
        if (action != null && onAction != null) ...[
          const SizedBox(height: 16),
          OutlinedButton(onPressed: onAction, child: Text(action!)),
        ],
      ]),
    ));
  }
}
