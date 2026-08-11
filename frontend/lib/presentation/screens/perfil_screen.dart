import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme.dart';
import '../../core/http/auth_client.dart';
import '../../data/datasources/auth_remote_ds.dart';
import '../providers/auth_provider.dart';
import '../widgets/app_bottom_nav.dart';
import '../widgets/clay.dart';

class PerfilScreen extends StatefulWidget {
  const PerfilScreen({super.key});

  @override
  State<PerfilScreen> createState() => _PerfilScreenState();
}

class _PerfilScreenState extends State<PerfilScreen> {
  String? _email;
  bool _cargando = true;

  @override
  void initState() {
    super.initState();
    AuthRemoteDataSource(AuthClient()).me().then((email) {
      if (mounted) setState(() { _email = email; _cargando = false; });
    }).catchError((_) {
      if (mounted) setState(() => _cargando = false);
    });
  }

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Scaffold(
      appBar: AppBar(title: const Text('Perfil')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          ClayContainer(
            child: Row(children: [
              Container(
                width: 44, height: 44,
                decoration: BoxDecoration(color: c.pitchSoft, borderRadius: BorderRadius.circular(12)),
                alignment: Alignment.center,
                child: Icon(Icons.person_outline_rounded, color: c.pitch),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  _cargando
                      ? Container(width: 140, height: 12, color: c.bg2)
                      : Text(_email ?? 'Sesión activa', style: TextStyle(fontWeight: FontWeight.w600, color: c.text, fontSize: 14)),
                  const SizedBox(height: 3),
                  Text('BetML Pro', style: TextStyle(color: c.textSecond, fontSize: 12)),
                ]),
              ),
            ]),
          ),
          const SizedBox(height: 24),
          OutlinedButton.icon(
            onPressed: () => context.read<AuthProvider>().logout(),
            icon: Icon(Icons.logout, color: c.brick, size: 18),
            label: Text('Cerrar sesión', style: TextStyle(color: c.brick)),
            style: OutlinedButton.styleFrom(side: BorderSide(color: c.brick), padding: const EdgeInsets.symmetric(vertical: 12)),
          ),
        ]),
      ),
      bottomNavigationBar: const AppBottomNav(current: AppTab.perfil),
    );
  }
}
