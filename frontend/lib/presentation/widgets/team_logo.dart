import 'package:flutter/material.dart';
import '../../core/theme.dart';

// Si no hay logo_url (equipo viejo, todavía no pasó por un fixture
// nuevo desde que guardador.py empezó a guardarlo) o falla la carga,
// cae a un círculo con la inicial — nunca un ícono roto.
class TeamLogo extends StatelessWidget {
  final String? url;
  final String nombre;
  final double size;
  const TeamLogo({super.key, required this.url, required this.nombre, this.size = 24});

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    if (url == null || url!.isEmpty) return _fallback(c);
    return ClipOval(
      child: Image.network(
        url!,
        width: size, height: size, fit: BoxFit.contain,
        errorBuilder: (_, __, ___) => _fallback(c),
        loadingBuilder: (_, child, progress) => progress == null ? child : _fallback(c),
      ),
    );
  }

  Widget _fallback(AppColors c) {
    return Container(
      width: size, height: size,
      decoration: BoxDecoration(color: c.bg2, shape: BoxShape.circle),
      alignment: Alignment.center,
      child: Text(
        nombre.isNotEmpty ? nombre[0].toUpperCase() : '?',
        style: TextStyle(fontSize: size * 0.42, fontWeight: FontWeight.w700, color: c.textSecond),
      ),
    );
  }
}
